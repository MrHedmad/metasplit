from metasplit.core import metasplit, MetaPath
from metasplit.bin import main
from tests.fixtures import test_matrix_data, test_selection_data


def test_metasplit(test_matrix_data, test_selection_data, tmp_path):
    query = f"{test_matrix_data}@id?col3=beta"
    output_file = tmp_path / "out.csv"
    metasplit(
        [MetaPath(query)],
        input_file=test_selection_data,
        output_file=output_file,
        ignore_missing=False,
        input_delimiter=",",
        always_include=["id5"]
    )

    written_data = output_file.open("r").read()
    expected = """id2,id4,id6,id5
b,d,f,e
h,j,l,k
n,p,r,q
t,v,x,w
"""
    assert written_data == expected
