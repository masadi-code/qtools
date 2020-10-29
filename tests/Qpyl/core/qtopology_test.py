from __future__ import absolute_import
from Qpyl.core.qparameter import QPrm
from Qpyl.core.qlibrary import QLib
from Qpyl.core.qstructure import QStruct
from Qpyl.core.qtopology import QTopology

def is_close(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def test_ff14sb_conversion():
    # Amber14FF to Qamber14 
    #
    # Convert Amber14 lib (+prepin for impropers) and parm+frcmod to Q lib/prm
    # Load the structure 'all_amino_acids.pdb' and build the topology
    # Check the total bonding energy contributions and number of bonding terms
    # and compare the library and parameter set with official qamber14.
    # 
    qal = QLib("amber")
    qap = QPrm("amber", ignore_errors=True) # duplicates
    qal.read_amber_lib("data/ff-amber14/amber12_mod.lib")
    qal.read_amber_lib("data/ff-amber14/arn.lib")
    qal.read_prepin_impropers("data/ff-amber14/prep/amino12.in")
    qal.read_prepin_impropers("data/ff-amber14/arn.prepi")
    qap.read_amber_parm("data/ff-amber14/parm/parm10.dat")
    qap.read_amber_frcmod("data/ff-amber14/parm/frcmod.ff14SB")

    # add options to parameters
    for line in """\
name                           Q-Amber14SB
type                           AMBER
vdw_rule                       arithmetic !vdW combination rule (geometric or arithmetic)
scale_14                       0.8333 ! electrostatic 1-4 scaling factor
switch_atoms                   off
improper_potential             periodic
improper_definition            explicit\
""".splitlines():
        lf = line.split()
        qap.options[lf[0]] = " ".join(lf[1:])

    # remove head from ACE and tail from NME
    cons = qal.residue_dict["ACE"].connections
    cons = [con for con in cons if "head" not in con]
    qal.residue_dict["ACE"].connections = cons

    cons = qal.residue_dict["NME"].connections
    cons = [con for con in cons if "tail" not in con]
    qal.residue_dict["NME"].connections = cons


    qas1 = QStruct("data/all_amino_acids.pdb", "pdb", ignore_errors=True)
    qat = QTopology(qal, qap, qas1)
    q_tors = sum([len(list(tor.prm.get_prms())) for tor in qat.torsions])

    assert len(qat.bonds) == 464
    assert len(qat.angles) == 829
    assert len(qat.torsions) == 1221
    assert q_tors == 1950
    assert len(qat.impropers) == 102

    be = sum([bond.energy for bond in qat.bonds])
    ae = sum([ang.energy for ang in qat.angles])
    te = sum([tor.energy for tor in qat.torsions])
    ie = sum([imp.energy for imp in qat.impropers])

    assert is_close(be, 181.2572830)
    assert is_close(ae, 212.8539304)
    assert is_close(te, 417.2919960)
    assert is_close(ie, 22.8171235)

    # compare with official lib
    qa14_lib = open("data/qamber14.lib", "r").read()
    qa14_prm = open("data/qamber14.prm", "r").read()

    #open("asd", "w").write(qap.get_string())

    assert qal.get_string() in qa14_lib
    assert qap.get_string() in qa14_prm
