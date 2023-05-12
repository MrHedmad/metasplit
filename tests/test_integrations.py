from metasplit.core import metasplit, MetaPath
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
    expected = """id2,id4,id5,id6
b,d,e,f
h,j,k,l
n,p,q,r
t,v,w,x
"""
    assert written_data == expected
