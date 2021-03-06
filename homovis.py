'''
This script gathers structures from a homologous protein family multiple sequence alignment input and generates an output of a collage of the images of a residue
of interest on each different structure generated from the input. To operate this script, the homologous protein library in stockholm format must be input,
along with the alignment number of the residue of interest. Optionally, the user may input a desired magnification for the generated images (default is z < 5)
'''
import ast
from Bio import AlignIO
from operator import itemgetter
import pandas as pd
import requests
import subprocess
import os
from varalign import alignments
import argparse
from PIL import Image


def parse_pdb_xrefs(seq):
    """
    Parse Pfam PDB dbxref annotations from sequence.

    Example: ['PDB; 4K7D B; 399-458;', 'PDB; 4K95 J; 399-458;']
    """
    pdb_xrefs = [x.split()[1:] for x in seq.dbxrefs if x.startswith('PDB;')]
    pdb_mappings = []
    for pdb_id, chain_id, res_range in pdb_xrefs:
        chain_id = chain_id.replace(';', '')
        start, end = map(int, res_range.replace(';', '').split('-'))  # Split start/end
        length = len(range(start, end + 1))  # Calculate length
        pdb_mappings.append((pdb_id, start, end, chain_id, length))
    return pdb_mappings


def chimera_command(pdb_id, start, end, chain_id, marked=None, name=None, template_n=0):
    """
    Construct Chimera command to open a PDB and isolat or mark a specific region.
    """
    # Select command template
    templates = ['open {pdb_id}; select #MODEL_ID:{start}-{end}.{chain_id}; select invert sel; delete sel',
                 'open {pdb_id}; setattr r domain true #MODEL_ID:{start}-{end}.{chain_id}; select #MODEL_ID:.{chain_id}; select invert sel; delete sel']
    template = templates[template_n]

    # Construct command from template and variables
    command = template.format(pdb_id=pdb_id, start=start, end=end, chain_id=chain_id)

    # Add marked attributes; format multi- or single-residue selection
    if isinstance(marked, (list, tuple)):
        marked = [str(x) + '.' + chain_id for x in marked]
        marked = ','.join(marked)
    elif isinstance(marked, str):
        marked += '.' + chain_id
    # Add to command
    if marked:
        command += '; setattr r marked true #MODEL_ID:{}'.format(marked)

    # Add name attribute setting to command
    if isinstance(name, str):
        command += '; setattr M name {} #MODEL_ID'.format(name)

    return command


def uniprot_pdb_query(uniprot_id):
    "Query SIFTS 'best_structures' endpoint."
    url = ''.join([sifts_best, uniprot_id])
    result = requests.get(url)
    return result.json()


def find_overlap(mapping, seq_range):
    "Calculate overlap between Pfam sequence and SIFTS mapped PDB."
    uniprot_resnums = range(*[mapping[k] for k in ('unp_start', 'unp_end')])
    covered = set(seq_range).intersection(set(uniprot_resnums))
    return (mapping['pdb_id'], mapping['chain_id'], len(covered) / float(len(seq_range)))


def uniprot_to_pdb(mapping):
    "Map UniProt residue numbers to PDB residue numbers."
    pdb_resnums = range(*[mapping[k] for k in ('start', 'end')])
    uniprot_resnums = range(*[mapping[k] for k in ('unp_start', 'unp_end')])
    return dict(zip(uniprot_resnums, pdb_resnums))





if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("alignment", help="Input the stockholm format alignment path to be analyzed.",
                        type=str)
    parser.add_argument("residue", help= "Input the residue you want to analyze.", type=int)
    parser.add_argument("magnification", help="Enter how many armstrongs the resolution of the images are to be.", type=int)
    parser.add_argument("Image_Width", help="Enter how many pixels the width of the images is to be.",
                        type=int)
    parser.add_argument("Image_Height", help="Enter how many pixels the height of the images is to be.",
                        type=int)
    args = parser.parse_args()

    alignment_path = args.alignment

    aln = AlignIO.read(alignment_path, 'stockholm')
    print aln



    #pdb_mappings = parse_pdb_xrefs(seq)
    #
    # # Read in columns from file
    # umd_family_info = '/homes/smacgowan/projects/umd_families/columns.csv'
    # column_table = pd.read_csv(umd_family_info,
    #                            index_col=0,
    #                            converters={'columns_pandas':ast.literal_eval})
    # column_table.head(2)
    #
    # alignment_name = alignment_path.split('/')[-1][:7]
    # umd_entry = column_table[column_table['AC'].str.contains(alignment_name)]
    # umd_entry
    #
    #umd_columns = umd_entry.get_value(122, 'columns_pandas')
    # umd_columns
    #
    # itemgetter(*umd_columns)(dict(alignments.index_seq_to_alignment(seq)))
    #
    #
    #
    #
    #
    # # Select example sequence mapped PDB (sort so that choice is first)
    # pdb_mappings.sort(key=lambda x: x[4], reverse=True)  # Sort by length
    # pdb_mappings.sort(key=lambda x: x[0], reverse=True)  # Sort by PDB
    #
    # # Lookup marked columns in example seq
    # marked = itemgetter(*umd_columns)(dict(alignments.index_seq_to_alignment(seq)))
    #
    # # Build command
    # command = chimera_command(*pdb_mappings[0][:-1], marked=marked, template_n=1)
    # command

    umd_columns = [args.residue]
    model = 0  # Initialise model ID
    # chimera_script = []
    # for seq in aln:
    #     if any([x.startswith('PDB') for x in seq.dbxrefs]):
    #         # Get PDB xrefs
    #         pdb_mappings = parse_pdb_xrefs(seq)
    #         pdb_mappings.sort(key=lambda x: x[4], reverse=True)  # Sort by length
    #         pdb_mappings.sort(key=lambda x: x[0], reverse=True)  # Sort by PDB
    #
    #         # Identify marked residue
    #         index_dict = dict(alignments.index_seq_to_alignment(seq))
    #         #marked = itemgetter(*umd_columns)(index_dict)
    #         marked = index_dict[umd_columns[0]]
    #
    #         # Write command
    #         command = chimera_command(*pdb_mappings[0][:-1], marked=marked)
    #         command = command.replace('MODEL_ID', str(model))  # Substitue model ID placeholder
    #
    #         chimera_script.append((seq.id, command))
    #         model += 1
    #
    # seqs_known_structure = zip(*chimera_script)[0]

    # Get SIFTS "best structure" for a sequence.
    sifts_best = 'http://www.ebi.ac.uk/pdbe/api/mappings/best_structures/'
    example = 'Q9JK66'

    result = uniprot_pdb_query(example)
    mapping = result[example][0]  # Extract first result from SIFTS query


    # Find overlaps for all retrieved SIFTS mappings
    seq_range = range(313, 378)  # Seq start/end for example sequence
    overlaps = [find_overlap(mapping, seq_range) for mapping in result[example]]
    overlaps.sort(key=lambda x: x[2], reverse=True)  # Reorder

    uniprot_to_pdb(mapping)

    model = 0  # Initialise model ID
    commands = []
    for seq in aln:
        if any([x.startswith('PDB') for x in seq.dbxrefs]):
            # if seq.id in seqs_known_structure:

            # Lookup PDBe mappings
            uniprot_id = seq.annotations['accession'].split('.')[0]
            try:
                pdb_mappings = uniprot_pdb_query(uniprot_id)[uniprot_id]
            except KeyError:
                print 'skipping {}'.format(uniprot_id)
                continue
            pdb_mappings = [x for x in pdb_mappings if x['experimental_method'] == 'X-ray diffraction']
            if len(pdb_mappings) == 0:
                continue

            # Identify pdb/chain with most overlap
            start, end = [seq.annotations[k] for k in ['start', 'end']]
            seq_range = range(start, end)
            overlaps = [find_overlap(mapping, seq_range) for mapping in pdb_mappings]
            overlaps.sort(key=lambda x: x[2], reverse=True)
            pdb_id, chain_id = overlaps[0][:2]
            # Find corresponding mapping
            for mapping in pdb_mappings:
                if mapping['pdb_id'] == pdb_id and mapping['chain_id'] == chain_id:
                    break

            # Identify start and end residues of PDB coverage
            res_map = uniprot_to_pdb(mapping)
            if start not in res_map.keys():
                start = min(res_map.keys())
            if end not in res_map.keys():
                end = max(res_map.keys())

            # PDB resnums
            pdb_start, pdb_end = [res_map[k] for k in [start, end]]

            # Marked columns
            try:
                marked = itemgetter(*umd_columns)(dict(alignments.index_seq_to_alignment(seq)))  ## umd_columns global
            except KeyError:
                marked = None
            if isinstance(marked, list):
                marked = [x for x in marked if x in res_map.keys()]
            if isinstance(marked, str):
                marked = [marked] if marked in res_map.keys() else []
            # Write command
            seq.id = seq.id.replace('/','_')
            model_name = seq.id + '({})'.format(pdb_id)
            #model_name = model_name.replace("/", "_")
            command = chimera_command(pdb_id, pdb_start, pdb_end, chain_id, marked, model_name, template_n=1) + '; wait'
            command = command.replace('MODEL_ID', str(model))
            commands.append((seq.id, pdb_id, chain_id, marked, command))
            model += 1

    chimera_script = list(zip(*commands)[4])
    chimera_script_model_length = len(chimera_script)

    # Add match maker
    # mm_script = ['mm #{} #{}; wait'.format('0', str(i+1)) for i in range(len(chimera_script)-1)]
    mm_script = ['mm #{}:/domain #{}:/domain; wait'.format('0', str(i + 1)) for i in
                 range(len(chimera_script) - 1)]
    # mm_script = ['mm #0 #1-{}; wait'.format(len(chimera_script)-1)]
    chimera_script = chimera_script + mm_script
    # Add quality of life commands
    chimera_script.append("display :/marked")
    chimera_script.append("focus :/marked z < {}".format(args.magnification))
    chimera_script.append("center :/marked")
    chimera_script.append("cofr :/marked")
    chimera_script.append("select :/marked; namesel marked")
    chimera_script.append("findhbond selRestrict \"marked & without CA/C1'\"reveal true intermodel false")
    # \n might work

    chimera_script = [x.replace("MODEL_ID", str(i))
                      for i, x in enumerate(chimera_script)]
    Session1_file_name = 'Manual_session_one.com'

    with open(Session1_file_name, 'w') as output:
        for line in chimera_script:
            output.write(line)
            output.write('\n')

    n = 0
    while n < len(commands):
        chimera_script.append("~modeldisp")
        chimera_script.append("modeldisp #{}".format(str(n)))
        chimera_script.append("rlabel marked")
        chimera_script.append(
            "copy file {}_{}_{}_{}.png png width {} height {}".format(commands[n][0], commands[n][1],
                                                                         commands[n][2], commands[n][3], args.Image_Width, args.Image_Height))
        chimera_script.append("~rlabel marked")
        n += 1

    manual_list = list()
    n = 0
    while n < len(commands):
        manual_list.append("~modeldisp")
        manual_list.append("modeldisp #{}".format(str(n)))
        manual_list.append("rlabel marked")
        manual_list.append(
            "copy file {}_{}_{}_{}.png png width {} height {}".format(commands[n][0], commands[n][1],
                                                                         commands[n][2], commands[n][3], args.Image_Width, args.Image_Height))
        manual_list.append("~rlabel marked")
        n += 1

    com_file_name = '{}_chimera_alignment.com'.format(args.alignment.split('/')[-1])
    Session2_file_name = 'Manual_session_two.com'

    cwd = os.getcwd()

    with open(com_file_name, 'w') as output:
        for line in chimera_script:
            output.write(line)
            output.write('\n')

    with open(Session2_file_name, 'w') as output:
        for line in manual_list:
            output.write(line)
            output.write('\n')


    subprocess.call(["chimera", "--nogui", com_file_name])