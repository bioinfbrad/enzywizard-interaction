from __future__ import annotations

from Bio.PDB import MMCIFParser, PDBParser, MMCIFIO, PDBIO
from Bio.PDB.Structure import Structure
from pathlib import Path

from ..utils.logging_utils import Logger
import json
import tempfile
from ..utils.common_utils import convert_to_json_serializable, InlineJSONEncoder, wrap_leaf_lists_as_rawjson, get_clean_filename, get_optimized_filename
from openmm.app import PDBFile,PDBxFile, Modeller
from typing import List, Dict,Any, Tuple
import subprocess
from rdkit import Chem
from ..utils.substrate_utils import is_valid_mol_3d




def file_exists(path: str | Path) -> bool:
    p = Path(path)
    return p.exists() and p.is_file()

def get_stem(input_path: str | Path) -> str:
    return Path(input_path).stem

MAXFILENAME=150

def check_filename_length(name: str, logger: Logger) -> bool:
    if len(name) > MAXFILENAME:
        logger.print(f"[ERROR] Filename too long (>{MAXFILENAME}): {name}")
        return False
    return True

def load_protein_structure(path: str | Path, protein_name:str, logger: Logger) -> Structure | None:
    p = Path(path)

    try:
        if p.suffix.lower() in {".cif", ".mmcif"}:
            parser = MMCIFParser(QUIET=True)
        elif p.suffix.lower() == ".pdb":
            parser = PDBParser(QUIET=True)
        else:
            logger.print(f"[ERROR] Unsupported format: {p}")
            return None

        return parser.get_structure(protein_name, str(p))

    except Exception as e:
        logger.print(f"[ERROR] Exception in loading structure for {str(p)}: {e}")
        return None





def write_json_from_dict(dict_data: dict, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    dict_data=convert_to_json_serializable(dict_data)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(dict_data, f, indent=2, ensure_ascii=False)

def write_json_from_dict_inline_leaf_lists(dict_data: dict, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    dict_data = convert_to_json_serializable(dict_data)
    dict_data = wrap_leaf_lists_as_rawjson(dict_data)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(
            dict_data,
            f,
            cls=InlineJSONEncoder,
            indent=2,
            ensure_ascii=False
        )




def write_sdf(mol_3d: Chem.Mol, sdf_path: str | Path, logger: Logger,) -> bool:
    if not is_valid_mol_3d(mol_3d, logger):
        return False

    try:
        sdf_path = Path(sdf_path)
        sdf_path.parent.mkdir(parents=True, exist_ok=True)

        writer = Chem.SDWriter(str(sdf_path))
        conf_id = mol_3d.GetConformer().GetId()
        writer.write(mol_3d, confId=conf_id)
        writer.close()

        if not sdf_path.exists() or sdf_path.stat().st_size <= 0:
            logger.print("[ERROR] Failed to save SDF file.")
            return False

        return True
    except Exception:
        logger.print("[ERROR] Failed to save Mol(3D) to SDF file.")
        return False




def load_sdf_mol_3d(sdf_path: str | Path, logger: Logger) -> Chem.Mol | None:
    try:
        sdf_path = Path(sdf_path)

        if not sdf_path.exists() or sdf_path.stat().st_size <= 0:
            logger.print("[ERROR] Invalid input SDF file.")
            return None

        supplier = Chem.SDMolSupplier(str(sdf_path), removeHs=False)
        if supplier is None or len(supplier) == 0:
            logger.print("[ERROR] Failed to load SDF file.")
            return None

        mol = supplier[0]
        if mol is None:
            logger.print("[ERROR] Failed to parse Mol from SDF file.")
            return None

        if mol.GetNumConformers() <= 0:
            logger.print("[ERROR] Input SDF does not contain 3D coordinates.")
            return None

        return mol

    except Exception:
        logger.print("[ERROR] Failed to read Mol(3D) from SDF file.")
        return None



def load_openmm_modeller(path: str | Path, logger) -> Modeller | None:
    if not isinstance(path, (str, Path)):
        logger.print("[ERROR] path must be a str or Path.")
        return None

    try:
        p = Path(path)
    except Exception:
        logger.print("[ERROR] Failed to parse path.")
        return None

    if not p.exists() or p.stat().st_size <= 0:
        logger.print(f"[ERROR] Invalid input structure file: {p}")
        return None

    try:
        suffix = p.suffix.lower()

        if suffix in {".cif", ".mmcif"}:
            obj = PDBxFile(str(p))
        elif suffix == ".pdb":
            obj = PDBFile(str(p))
        else:
            logger.print(f"[ERROR] Unsupported structure format: {p}")
            return None

        return Modeller(obj.topology, obj.positions)

    except Exception:
        logger.print(f"[ERROR] Failed to load OpenMM Modeller from {str(p)}")
        return None

def load_substrate_name_and_mol_3d_list(substrate_names: str,substrate_dir: str | Path,logger: Logger) -> Tuple[List[str], List[Chem.Mol]] | None:
    if not isinstance(substrate_names, str) or not substrate_names.strip():
        logger.print("[ERROR] substrate_names is empty.")
        return None

    if not isinstance(substrate_dir, (str, Path)):
        logger.print("[ERROR] substrate_dir must be a str or Path.")
        return None

    try:
        substrate_dir = Path(substrate_dir)
    except Exception:
        logger.print("[ERROR] Failed to parse substrate_dir.")
        return None

    if not substrate_dir.exists() or not substrate_dir.is_dir():
        logger.print(f"[ERROR] Invalid substrate_dir: {substrate_dir}")
        return None

    substrate_name_list = [x.strip() for x in str(substrate_names).split(",")]
    if len(substrate_name_list) == 0:
        logger.print("[ERROR] substrate_names is empty.")
        return None

    if any(not x for x in substrate_name_list):
        logger.print("[ERROR] substrate_names contains empty substrate name.")
        return None

    if len(set(substrate_name_list)) != len(substrate_name_list):
        logger.print("[ERROR] Duplicate substrate names are not allowed.")
        return None

    mol_3d_list: List[Chem.Mol] = []

    for substrate_name in substrate_name_list:
        substrate_file_stem = get_optimized_filename(substrate_name)
        if not substrate_file_stem:
            logger.print(f"[ERROR] Invalid substrate filename generated from substrate: {substrate_name}")
            return None

        sdf_path = substrate_dir / f"{substrate_file_stem}.sdf"

        if not sdf_path.exists() or not sdf_path.is_file():
            logger.print(f"[ERROR] Substrate SDF not found: {sdf_path}")
            return None

        mol_3d = load_sdf_mol_3d(sdf_path, logger)
        if mol_3d is None:
            logger.print(f"[ERROR] Failed to load Mol(3D) from SDF: {sdf_path}")
            return None

        mol_3d_list.append(mol_3d)

    return substrate_name_list, mol_3d_list