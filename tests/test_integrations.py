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
        always_include=["id5"],
    )

    written_data = output_file.open("r").read()
    expected = """id2,id4,id5,id6
b,d,e,f
h,j,k,l
n,p,q,r
t,v,w,x
"""
    assert written_data == expected


def test_and(test_matrix_data, test_selection_data, tmp_path):
    query = f"{test_matrix_data}@id?col3=beta&col1!=[d,e,f]"
    output_file = tmp_path / "out.csv"
    metasplit(
        [MetaPath(query)],
        input_file=test_selection_data,
        output_file=output_file,
        ignore_missing=False,
        input_delimiter=",",
        always_include=["id5"],
    )

    written_data = output_file.open("r").read()
    expected = """id2,id5
b,e
h,k
n,q
t,w
"""
    assert written_data == expected


def test_or(test_matrix_data, test_selection_data, tmp_path):
    query = f"{test_matrix_data}@id?col3=beta|col1!=[d,e,f]"
    output_file = tmp_path / "out.csv"
    metasplit(
        [MetaPath(query)],
        input_file=test_selection_data,
        output_file=output_file,
        ignore_missing=False,
        input_delimiter=",",
        always_include=None,
    )

    written_data = output_file.open("r").read()
    expected = """id1,id2,id3,id4,id6
a,b,c,d,f
g,h,i,j,l
m,n,o,p,r
s,t,u,v,x
"""
    assert written_data == expected


def test_double_and(test_matrix_data, test_selection_data, tmp_path):
    query = f"{test_matrix_data}@id?col3=beta&col1=[a,b,c]&col1!=a"
    output_file = tmp_path / "out.csv"
    metasplit(
        [MetaPath(query)],
        input_file=test_selection_data,
        output_file=output_file,
        ignore_missing=False,
        input_delimiter=",",
        always_include=None,
    )

    written_data = output_file.open("r").read()
    expected = """id2
b
h
n
t
"""
    assert written_data == expected


def test_and_or(test_matrix_data, test_selection_data, tmp_path):
    query = f"{test_matrix_data}@id?col3=beta|col1=[a,b,c]&col1!=a"
    output_file = tmp_path / "out.csv"
    metasplit(
        [MetaPath(query)],
        input_file=test_selection_data,
        output_file=output_file,
        ignore_missing=False,
        input_delimiter=",",
        always_include=None,
    )

    written_data = output_file.open("r").read()
    expected = """id2,id3,id4,id6
b,c,d,f
h,i,j,l
n,o,p,r
t,u,v,x
"""
    assert written_data == expected


def test_two_query(test_matrix_data, test_selection_data, tmp_path):
    query = f"{test_matrix_data}@id?col1=a"
    query2 = f"{test_matrix_data}@id?col2=1"
    output_file = tmp_path / "out.csv"
    metasplit(
        [MetaPath(query), MetaPath(query2)],
        input_file=test_selection_data,
        output_file=output_file,
        ignore_missing=False,
        input_delimiter=",",
        always_include=None,
    )

    written_data = output_file.open("r").read()
    expected = """id1,id4
a,d
g,j
m,p
s,v
"""
    assert written_data == expected


def test_two_query_intersection(test_matrix_data, test_selection_data, tmp_path):
    query = f"{test_matrix_data}@id?col1=a"
    query2 = f"{test_matrix_data}@id?col3=alpha"
    output_file = tmp_path / "out.csv"
    metasplit(
        [MetaPath(query), MetaPath(query2)],
        input_file=test_selection_data,
        output_file=output_file,
        intersect=True,
        ignore_missing=False,
        input_delimiter=",",
        always_include=None,
    )

    written_data = output_file.open("r").read()
    expected = """id1
a
g
m
s
"""
    assert written_data == expected
