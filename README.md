[![DOI](https://zenodo.org/badge/1219038253.svg)](https://doi.org/10.5281/zenodo.19709914)
# EnzyWizard-Interaction

EnzyWizard-Interaction is a command-line tool for calculating protein/protein-substrate
molecular interactions and generating a detailed JSON report.
It takes a cleaned CIF or PDB protein structure and a substrate directory as input and supports
protein-(multi)substrate(s) molecular interaction analysis. The tool detects six types of molecular interactions:
hydrogen bond, ionic bond, van der Waals contact, pi-pi stacking,
pi-cation interaction, disulfide bond.
The geometric definitions and molecular interaction calculation formula follow
the residue interaction network methods RING4.
To improve efficiency, the program uses vectorized geometry operations and
KD-tree accelerated neighbour searching, enabling fast
molecular interaction detection on protein / protein-substrate systems.
The tool outputs structured molecular interaction records and summarized statistics
suitable for downstream applications such as enzyme-substrate molecular interaction
analysis and residue interaction graph construction.


# Documentation index:

- example usage
- input parameters
- output files
- output report schema
- Process
- common errors and solutions
- dependencies
- references


# example usage:

The examples below use placeholder paths such as `path/to/input.cif`,
`path/to/substrate_dir/`, and `path/to/output_dir/`; replace them with your own
cleaned protein structure file, docked substrate SDF directory, and output
directory. Substrate names are provided with `-s` and must match docked SDF file
names in `--substrate_dir`. For example, `docked_glucose` matches
`docked_glucose.sdf`.

Calculate intra-protein molecular interactions from a cleaned CIF structure
using default interaction cutoffs. Omitting both `--substrate_names` and
`--substrate_dir` runs protein-only interaction analysis.

```
enzywizard-interaction -i path/to/input.cif -o path/to/output_dir/
```

Calculate intra-protein molecular interactions from a cleaned PDB structure.

```
enzywizard-interaction -i path/to/input.pdb -o path/to/output_pdb/
```

Calculate protein-substrate interactions for one docked substrate. The substrate
name must match an SDF file in the substrate directory.

```
enzywizard-interaction -i path/to/input.cif -s "docked_glucose" -d path/to/substrate_dir/ -o path/to/output_single_substrate/
```

Calculate interactions for multiple docked substrates in the same protein
structure. Multiple substrate names are separated by semicolons.

```
enzywizard-interaction -i path/to/input.cif -s "docked_glucose;docked_fructose" -d path/to/substrate_dir/ -o path/to/output_multi_substrate/
```

Use long option names for the same multi-substrate workflow.

```
enzywizard-interaction --input_path path/to/input.cif --substrate_names "docked_glucose;docked_fructose" --substrate_dir path/to/substrate_dir/ --output_dir path/to/output_long_options/
```

Use stricter hydrogen-bond geometry. Smaller distance cutoffs and a larger
minimum angle make hydrogen-bond detection more selective and may reduce false
positive interactions, but may miss weak or borderline hydrogen bonds.

```
enzywizard-interaction -i path/to/input.cif -s "docked_glucose" -d path/to/substrate_dir/ -o path/to/output_strict_hbonds/ --hbond_da_max_distance 3.2 --hbond_ha_max_distance 2.1 --hbond_angle 120
```

Use more permissive hydrogen-bond geometry. Larger distance cutoffs and a
smaller minimum angle may recover weaker or less ideal hydrogen bonds, but can
increase the number of reported interactions and candidate geometry checks.

```
enzywizard-interaction -i path/to/input.cif -s "docked_glucose" -d path/to/substrate_dir/ -o path/to/output_permissive_hbonds/ --hbond_da_max_distance 4.2 --hbond_ha_max_distance 2.8 --hbond_angle 75
```

Use a stricter ionic-bond distance cutoff. A smaller cutoff reports only closer
oppositely charged centers and can reduce borderline ionic contacts.

```
enzywizard-interaction -i path/to/input.cif -s "docked_glucose" -d path/to/substrate_dir/ -o path/to/output_strict_ionic/ --ionic_distance_cutoff 3.2
```

Use broader aromatic and pi-cation cutoffs. Larger distance cutoffs can include
more candidate ring-ring and ring-cation contacts, which may increase reported
interactions and runtime. A larger pi-cation angle cutoff is more permissive for
ring-cation geometry.

```
enzywizard-interaction -i path/to/input.cif -s "docked_glucose;docked_fructose" -d path/to/substrate_dir/ -o path/to/output_broad_aromatic/ --ppstack_center_distance_cutoff 7.5 --pication_distance_cutoff 6.5 --pication_angle_cutoff 60
```

Use a stricter disulfide-bond cutoff. A smaller sulfur-sulfur distance cutoff
reports only tighter disulfide bonds, while a larger cutoff is more permissive
and may include borderline cysteine pairs.

```
enzywizard-interaction -i path/to/input.cif -o path/to/output_strict_ssbond/ --ssbond_max_distance 2.1
```


# input parameters:

-i, --input_path
Required.
Path to the cleaned protein structure file used for interaction calculation.
Supported file extensions: .cif, .pdb.
The structure should already be cleaned and should contain a single protein
chain suitable for downstream OpenMM and Biopython parsing.

-s, --substrate_names
Optional.
Substrate names separated by semicolons.

Examples:
- docked_glucose
- docked_glucose;docked_fructose

Each substrate name is converted to a file stem and must match one docked SDF
file in --substrate_dir. For example, `docked_glucose` is read from
`docked_glucose.sdf`.
Empty substrate names and duplicate substrate names are not allowed.

If --substrate_names and --substrate_dir are both omitted, the program only
calculates intra-protein molecular interactions.
If one of --substrate_names and --substrate_dir is provided, the other one must
also be provided.

-d, --substrate_dir
Optional.
Path to the directory containing docked substrate SDF files.
This parameter must be provided together with --substrate_names and omitted when
--substrate_names is omitted.
The program reads only the matched `.sdf` files requested by --substrate_names.
Each SDF file must contain a molecule with 3D coordinates.

-o, --output_dir
Required.
Directory to save the interaction JSON report.
The output directory is created automatically if it does not exist.

--hbond_da_max_distance
Optional.
Maximum donor-acceptor distance cutoff for hydrogen bond detection.
Unit: angstroms (A).
Default: 3.9.
Valid range: 2.5 to 4.5.
Larger values are more permissive and may report more hydrogen bonds; smaller
values are stricter and may miss weak or long hydrogen bonds.

--hbond_ha_max_distance
Optional.
Maximum hydrogen-acceptor distance cutoff for hydrogen bond detection.
Unit: angstroms (A).
Default: 2.5.
Valid range: 1.5 to 3.0.
Larger values are more permissive and may report more hydrogen bonds; smaller
values are stricter and may miss weak or long hydrogen bonds.

--hbond_angle
Optional.
Minimum donor-hydrogen-acceptor angle cutoff for hydrogen bond detection in degrees.
Unit: degrees.
Default: 90.0.
Valid range: 60 to 180.
Larger values require more linear donor-hydrogen-acceptor geometry and are more
selective; smaller values are more permissive and may report less ideal
hydrogen-bond geometries.

--ionic_distance_cutoff
Optional.
Maximum distance cutoff for ionic bond detection.
Unit: angstroms (A).
Default: 4.0.
Valid range: 2.0 to 6.0.
Larger values include more distant charged centers and may report more ionic
contacts; smaller values keep only closer charged centers.

--ppstack_center_distance_cutoff
Optional.
Maximum aromatic ring-center distance cutoff for pi-pi stacking detection.
Unit: angstroms (A).
Default: 6.5.
Valid range: 4.0 to 8.0.
Larger values include more candidate aromatic ring pairs and may increase both
reported pi-pi stacking interactions and runtime; smaller values are more
selective.

--pication_distance_cutoff
Optional.
Maximum ring-cation distance cutoff for pi-cation interaction detection.
Unit: angstroms (A).
Default: 5.0.
Valid range: 3.0 to 7.0.
Larger values include more ring-cation candidates and may increase both reported
pi-cation interactions and runtime; smaller values are more selective.

--pication_angle_cutoff
Optional.
Maximum angle cutoff for pi-cation interaction detection in degrees.
Unit: degrees.
Default: 45.0.
Valid range: 0 to 90.
Larger values are more permissive for ring-cation geometry; smaller values
require a tighter geometry and may reduce borderline pi-cation interactions.

--ssbond_max_distance
Optional.
Maximum sulfur-sulfur distance cutoff for disulfide bond detection.
Unit: angstroms (A).
Default: 2.5.
Valid range: 1.8 to 3.0.
Larger values are more permissive and may include borderline cysteine pairs;
smaller values report only tighter disulfide bonds.


# output files:

The program outputs the following files into the output directory:

`{protein_name}` is derived from the input structure file name without its
extension.

1. A JSON report
   - interaction_report_{protein_name}.json
     - Generated when only intra-protein interactions are calculated.
   - interaction_report_{protein_name}_{substrate_names}.json
     - Generated when substrate names are provided.
   - JSON report containing molecular interaction records and summarized
     interaction statistics.

2. A log file
   - log.txt
     - Processing log containing informational messages, warnings, and errors.


# output report schema:

The JSON report contains the following fields:

   - "report_type"
     - Data type: string
     - Expected value: "enzywizard_interaction"
     - Description: The field 'report_type' indicates the type of report ('report': http://purl.obolibrary.org/obo/IAO_0000088) generated by the EnzyWizard-Interaction software.

   - "molecular_interactions"
     - Data type: array
     - Description: The field 'molecular_interactions' indicates the molecular interactions ('molecular interaction': https://bioportal.bioontology.org/ontologies/MI) between residues ('residue': http://purl.obolibrary.org/obo/GENO_0000782) in the enzyme ('enzyme': https://purl.dsmz.de/schema/Enzyme), or between residues and substrates ('substrate': https://purl.dsmz.de/schema/Substrate).

     Each item in "molecular_interactions" is an object containing:

     - "molecular_interaction_type"
       - Data type: string
       - Allowed values: HBOND, IONIC, VDW, PIPISTACK, PICATION, SSBOND.
       - Description: The field 'molecular_interaction_type' indicates the type ('interaction type': http://purl.obolibrary.org/obo/MI_0190) of molecular interaction ('molecular interaction': https://bioportal.bioontology.org/ontologies/MI), using RING interaction codes ('RING interaction type': https://ring.biocomputingup.it/help/interactions): hydrogen bond ('hydrogen bond': https://goldbook.iupac.org/terms/view/H02899; value: HBOND), ionic bond ('ionic bond': https://goldbook.iupac.org/terms/view/IT07058; value: IONIC), van der Waals contact ('van der Waals forces': https://goldbook.iupac.org/terms/view/V06597; value: VDW), pi-pi stacking ('pi-pi stacking': https://goldbook.iupac.org/terms/view/13861; value: PIPISTACK), pi-cation interaction ('cation-pi interaction': https://goldbook.iupac.org/terms/view/08154; value: PICATION), and disulfide bond ('disulfide bond': https://www.uniprot.org/help/disulfid; value: SSBOND).

     - "source_node"
       - Data type: object
       - Description: The field 'source_node' indicates the source node ('node': https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/#graphdb-node) corresponding to a residue ('residue': http://purl.obolibrary.org/obo/GENO_0000782) or substrate ('substrate': https://purl.dsmz.de/schema/Substrate) in a molecular interaction ('molecular interaction': https://bioportal.bioontology.org/ontologies/MI).

     - "target_node"
       - Data type: object
       - Description: The field 'target_node' indicates the target node ('node': https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/#graphdb-node) corresponding to a residue ('residue': http://purl.obolibrary.org/obo/GENO_0000782) or substrate ('substrate': https://purl.dsmz.de/schema/Substrate) in a molecular interaction ('molecular interaction': https://bioportal.bioontology.org/ontologies/MI).

     The "source_node" and "target_node" objects are either residue nodes or
     substrate nodes.

     Residue node contains:

     - "residue_index"
       - Data type: integer
       - Description: The field 'residue_index' indicates the index ('index': http://purl.obolibrary.org/obo/NCIT_C25390) of the residue ('residue': http://purl.obolibrary.org/obo/GENO_0000782).

     - "residue_name"
       - Data type: string
       - Allowed values: A, C, D, E, F, G, H, I, K, L, M, N, P, Q, R, S, T, V, W, Y.
       - Description: The field 'residue_name' indicates the name of the residue ('residue': http://purl.obolibrary.org/obo/GENO_0000782), using one-letter code ('one-letter code': https://iupac.qmul.ac.uk/AminoAcid/A2021.html) to represent.

     - "node_type"
       - Data type: string
       - Expected value: "residue"
       - Description: The field 'node_type' indicates the type of node ('node': https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/#graphdb-node), with value 'residue' indicating a residue ('residue': http://purl.obolibrary.org/obo/GENO_0000782).

     Substrate node contains:

     - "substrate_index"
       - Data type: integer
       - Description: The field 'substrate_index' indicates the index ('index': http://purl.obolibrary.org/obo/NCIT_C25390) of the substrate ('substrate': https://purl.dsmz.de/schema/Substrate).

     - "substrate_name"
       - Data type: string
       - Description: The field 'substrate_name' indicates the name of the substrate ('substrate': https://purl.dsmz.de/schema/Substrate).

     - "node_type"
       - Data type: string
       - Expected value: "substrate"
       - Description: The field 'node_type' indicates the type of node ('node': https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/#graphdb-node), with value 'substrate' indicating a substrate ('substrate': https://purl.dsmz.de/schema/Substrate).

   - "molecular_interaction_statistics"
     - Data type: object
     - Description: The field 'molecular_interaction_statistics' indicates the summary statistics ('statistics': http://purl.obolibrary.org/obo/STATO_0000039) of molecular interactions ('molecular interaction': https://bioportal.bioontology.org/ontologies/MI).

     The "molecular_interaction_statistics" object contains:

     - "overall_molecular_interaction_statistics"
       - Data type: object
       - Description: The field 'overall_molecular_interaction_statistics' indicates the summary statistics ('statistics': http://purl.obolibrary.org/obo/STATO_0000039) of all molecular interactions ('molecular interaction': https://bioportal.bioontology.org/ontologies/MI), including intra-enzyme interactions and enzyme-substrate interactions.

     - "intra_enzyme_interaction_statistics"
       - Data type: object
       - Description: The field 'intra_enzyme_interaction_statistics' indicates the summary statistics ('statistics': http://purl.obolibrary.org/obo/STATO_0000039) of intra-enzyme molecular interactions ('molecular interaction': https://bioportal.bioontology.org/ontologies/MI) between residues ('residue': http://purl.obolibrary.org/obo/GENO_0000782) in the enzyme ('enzyme': https://purl.dsmz.de/schema/Enzyme).

     - "enzyme_substrate_interaction_statistics"
       - Data type: object
       - Description: The field 'enzyme_substrate_interaction_statistics' indicates the summary statistics ('statistics': http://purl.obolibrary.org/obo/STATO_0000039) of molecular interactions ('molecular interaction': https://bioportal.bioontology.org/ontologies/MI) between residues ('residue': http://purl.obolibrary.org/obo/GENO_0000782) in the enzyme ('enzyme': https://purl.dsmz.de/schema/Enzyme) and substrates ('substrate': https://purl.dsmz.de/schema/Substrate).

     Each statistics object contains:

     - "hydrogen_bond_count"
       - Data type: integer
       - Description: The field 'hydrogen_bond_count' indicates the count of hydrogen bonds ('hydrogen bond': https://goldbook.iupac.org/terms/view/H02899).

     - "ionic_bond_count"
       - Data type: integer
       - Description: The field 'ionic_bond_count' indicates the count of ionic bonds ('ionic bond': https://goldbook.iupac.org/terms/view/IT07058).

     - "van_der_waals_contact_count"
       - Data type: integer
       - Description: The field 'van_der_waals_contact_count' indicates the count of van der Waals contacts ('van der Waals forces': https://goldbook.iupac.org/terms/view/V06597).

     - "pi_pi_stacking_count"
       - Data type: integer
       - Description: The field 'pi_pi_stacking_count' indicates the count of pi-pi stacking interactions ('pi-pi stacking': https://goldbook.iupac.org/terms/view/13861).

     - "pi_cation_interaction_count"
       - Data type: integer
       - Description: The field 'pi_cation_interaction_count' indicates the count of pi-cation interactions ('cation-pi interaction': https://goldbook.iupac.org/terms/view/08154).

     - "disulfide_bond_count"
       - Data type: integer
       - Description: The field 'disulfide_bond_count' indicates the count of disulfide bonds ('disulfide bond': https://www.uniprot.org/help/disulfid).


# Process:

This command processes the input cleaned protein structure as follows:

1. Load the input structure
   - Read the cleaned CIF or PDB file using Biopython (Bio.PDB).
   - Resolve the protein name from the input filename.

2. Validate input conditions
   - Check that the input file exists.
   - Validate that the structure satisfies the cleaned-structure requirement.
   - Validate molecular interaction cutoff parameters.

3. Load OpenMM modeller
   - Read the same input structure as an OpenMM Modeller object.
   - Build coordinate-based protein representation for geometric molecular interaction calculation.

4. Check hydrogen completeness
   - Detect whether the protein structure contains hydrogen atoms.
   - Report warnings if hydrogen atoms are missing or too few.

5. Parse substrate inputs
   - Determine whether the program runs in:
     - protein-only mode
     - protein-substrate mode

6. Load docked substrates
   - If substrate_names and substrate_dir are provided, search substrate_dir for matched docked substrate SDF files.
   - Load matched SDF files as substrate Mol(3D) objects.

7. Filter substrate molecules
   - Check whether each substrate molecule is a valid 3D structure.
   - Check whether explicit hydrogen atoms are present.
   - Check whether the substrate is spatially docked to the protein.
   - Retain valid substrates for molecular interaction calculation.

8. Build geometric tables
   - Convert OpenMM coordinates from nm to Å.
   - Build protein atom/bond tables.
   - Build substrate atom/bond tables.

9. Detect hydrogen bonds
   - Identify protein donor and acceptor atoms from backbone and side-chain functional groups.
   - Identify substrate donor and acceptor atoms using RDKit chemical features.
   - Detect hydrogen bonds using distance and angle constraints.

10. Detect ionic bonds
   - Build charged centers for protein residues and substrate atoms.
   - Detect oppositely charged center pairs within the distance cutoff.

11. Detect van der Waals contacts
   - Assign van der Waals radii based on atom element type.
   - Detect atom pairs whose distances satisfy radius-sum contact constraints.

12. Detect pi-pi stacking
   - Identify protein aromatic rings from residue templates.
   - Identify substrate aromatic rings using RDKit aromatic ring information.
   - Detect ring pairs using ring-center distance cutoff.

13. Detect pi-cation interactions
   - Identify aromatic rings and cation centers from protein and substrate.
   - Detect ring-cation pairs using distance and angle constraints.

14. Detect disulfide bonds
   - Identify cysteine SG atoms from protein.
   - Detect sulfur-sulfur pairs using distance cutoff.

15. Merge molecular interaction records
   - Convert all detected raw edges into standardized molecular interaction records.
   - Build node information for residue nodes and substrate nodes.
   - Sort molecular interaction records into a stable output order.

16. Summarize molecular interaction statistics
   - Count detected molecular interactions for:
     - all molecular interactions
     - intra-protein molecular interactions
     - protein-substrate molecular interactions

17. Save outputs
   - Generate and save a JSON report containing molecular interaction records and summary statistics.


# common errors and solutions:

- "Input not found"
  - Cause: The path passed to `-i` or `--input_path` does not exist or is not a file.
  - Solution: Check the input file path and make sure it points to an existing cleaned CIF or PDB file.

- "Filename too long"
  - Cause: The input file name without extension is longer than the supported filename limit.
  - Solution: Rename the input file to a shorter name and run the command again.

- "Unsupported format"
  - Cause: The input structure extension is not `.cif` or `.pdb`.
  - Solution: Use a supported cleaned structure file format.

- "Failed to load protein structure"
  - Cause: Biopython could not parse the input file as a usable protein structure, or the file is empty, corrupted, or inconsistent with its extension.
  - Solution: Check that the input is a valid cleaned CIF or PDB structure file.

- "Failed to load OpenMM Modeller"
  - Cause: OpenMM could not parse the same input structure for coordinate-based interaction calculation.
  - Solution: Check that the structure file is valid, non-empty, and readable by OpenMM. If needed, rerun `enzywizard-clean` and use its cleaned output.

- "Cleaned structure validation failed"
  - Cause: The input is not a valid EnzyWizard-cleaned single-chain protein structure. Common causes include multiple chains, non-chain-A input, heterogens, insertion codes, non-standard residues, missing atoms, unexpected atoms, invalid occupancies, or non-continuous numbering.
  - Solution: Review the specific validation error above this summary in `log.txt`, run `enzywizard-clean`, and use its cleaned CIF or PDB output.

- "Protein structure does not contain hydrogen atoms. Please run 'enzywizard clean' first."
  - Cause: Hydrogen atoms are missing from the cleaned protein structure.
  - Solution: Run `enzywizard-clean` with hydrogen addition enabled, then rerun interaction calculation.

- "Protein structure contains few hydrogen atoms. It is recommended to run 'enzywizard clean' first."
  - Cause: The protein contains fewer hydrogens than expected, which can reduce hydrogen-bond detection quality.
  - Solution: Rerun `enzywizard-clean` with hydrogen addition enabled if hydrogen-bond detection is important.

- "substrate_names and substrate_dir must be provided together, or both omitted."
  - Cause: Only one of `--substrate_names` and `--substrate_dir` was provided.
  - Solution: Provide both parameters for protein-substrate interaction analysis, or omit both for protein-only analysis.

- "Invalid substrate_dir"
  - Cause: The path passed to `-d` or `--substrate_dir` does not exist or is not a directory.
  - Solution: Check that `--substrate_dir` points to a directory containing docked substrate SDF files.

- "substrate_names contains empty substrate name."
  - Cause: The semicolon-separated substrate list contains an empty item, such as a trailing semicolon or two semicolons in a row.
  - Solution: Remove empty items and use a value such as `docked_glucose;docked_fructose`.

- "Duplicate substrate names are not allowed."
  - Cause: The same substrate name appears more than once in `--substrate_names`.
  - Solution: Remove duplicate names from the semicolon-separated substrate list.

- "Substrate SDF not found"
  - Cause: No SDF file in `--substrate_dir` matches one of the requested substrate names.
  - Solution: Make sure each substrate name matches one docked SDF file, such as `docked_glucose.sdf`.

- "Invalid input SDF file."
  - Cause: A matched substrate SDF file is missing, empty, or not a regular file.
  - Solution: Check that each requested substrate SDF file exists and is non-empty.

- "Failed to parse Mol from SDF file."
  - Cause: RDKit could not parse a matched SDF file as a molecule.
  - Solution: Regenerate the substrate SDF file and confirm it contains a valid small-molecule structure.

- "Input SDF does not contain 3D coordinates."
  - Cause: A matched substrate SDF file does not contain a 3D conformer.
  - Solution: Generate a 3D substrate SDF, for example with `enzywizard-substrate`, and use the docked SDF output from `enzywizard-dock`.

- "Failed to filter valid docked substrate(s)"
  - Cause: No requested substrate passed validation as a usable docked 3D molecule near the protein. Common causes include invalid Mol(3D), missing explicit hydrogens, or coordinates not spatially docked to the protein.
  - Solution: Use `enzywizard-substrate` to generate valid 3D substrate structures and `enzywizard-dock` to generate docked substrate structures, then rerun interaction calculation.

- "da_max_distance_A out of range [2.5, 4.5]"
  - Cause: The value passed to `--hbond_da_max_distance` is outside the supported range.
  - Solution: Use a value from 2.5 to 4.5.

- "ha_max_distance_A out of range [1.5, 3.0]"
  - Cause: The value passed to `--hbond_ha_max_distance` is outside the supported range.
  - Solution: Use a value from 1.5 to 3.0.

- "dha_min_angle_deg out of range [60, 180]"
  - Cause: The value passed to `--hbond_angle` is outside the supported range.
  - Solution: Use a value from 60 to 180.

- "ionic_distance_cutoff_A out of range [2.0, 6.0]"
  - Cause: The value passed to `--ionic_distance_cutoff` is outside the supported range.
  - Solution: Use a value from 2.0 to 6.0.

- "ring_center_distance_cutoff_A out of range [4.0, 8.0]"
  - Cause: The value passed to `--ppstack_center_distance_cutoff` is outside the supported range.
  - Solution: Use a value from 4.0 to 8.0.

- "ring_cation_distance_cutoff_A out of range [3.0, 7.0]"
  - Cause: The value passed to `--pication_distance_cutoff` is outside the supported range.
  - Solution: Use a value from 3.0 to 7.0.

- "ring_cation_angle_cutoff_deg out of range [0, 90]"
  - Cause: The value passed to `--pication_angle_cutoff` is outside the supported range.
  - Solution: Use a value from 0 to 90.

- "ss_max_distance_A out of range [1.8, 3.0]"
  - Cause: The value passed to `--ssbond_max_distance` is outside the supported range.
  - Solution: Use a value from 1.8 to 3.0.

- "Failed to calculate interaction network."
  - Cause: One of the interaction-detection steps failed while building geometric tables or detecting molecular interactions.
  - Solution: Review the specific error above this summary in `log.txt`, then check the cleaned protein structure, substrate SDF files, and cutoff values.

- "Failed to write report JSON"
  - Cause: The JSON report could not be written to the output directory because of a filesystem, permission, path, or disk-space problem.
  - Solution: Check that the `-o` output directory path is writable and that there is enough disk space.

- Output files are missing
  - Cause: The command failed before all output files were written, or the output directory is not the one expected.
  - Solution: Check `log.txt`, confirm the `-o` output directory, and rerun after fixing earlier errors.

- Output file names are different from expected
  - Cause: Output names are derived from the input structure file name and, in protein-substrate mode, the substrate names.
  - Solution: Check the input file name, the substrate names, and the output mode. Look for `interaction_report_{protein_name}.json`, `interaction_report_{protein_name}_{substrate_names}.json`, and `log.txt` in the output directory.


# dependencies:

- RDKit
- OpenMM
- Biopython
- NumPy
- SciPy


# references:

- Martin et al., RING 4.0: residue interaction network generation for protein structures and ensembles
  https://ring.biocomputingup.it/about

- Piovesan et al., RING 2.0: fast generation of residue interaction networks
  https://doi.org/10.1093/bioinformatics/btw203

- Bondi, A. van der Waals Volumes and Radii
  J. Phys. Chem. 1964, 68, 3, 441–451
  https://doi.org/10.1021/j100785a001

- RDKit:
  https://www.rdkit.org/

- OpenMM:
  https://openmm.org/

- Biopython:
  https://biopython.org/
