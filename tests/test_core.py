from metasplit import core
from tests.fixtures import test_matrix_data, test_tsv_data

from pathlib import Path

def test_tests():
    assert True, "Everything is awesome!"


CONSUME_RESULTS = {
    "?var_1=val_1": core.Selection(
        filter_variable="var_1",
        sign=core.SelectionSign.EQUAL_TO,
        union=core.UnionSign.POSITIVE,
        filter_values=["val_1"]
    ),
    "&some_very_long_var=someverylongvalue": core.Selection(
        filter_variable="some_very_long_var",
        sign=core.SelectionSign.EQUAL_TO,
        union=core.UnionSign.NEGATIVE,
        filter_values=["someverylongvalue"]
    ),
    "|abbaabbaabba=bubbabubbabubba": core.Selection(
        filter_variable="abbaabbaabba",
        sign=core.SelectionSign.EQUAL_TO,
        union=core.UnionSign.POSITIVE,
        filter_values=["bubbabubbabubba"]
    ),
    "?var_1!=val_1": core.Selection(
        filter_variable="var_1",
        sign=core.SelectionSign.NOT_EQUAL_TO,
        union=core.UnionSign.POSITIVE,
        filter_values=["val_1"]
    ),
    "&var_1!=val_1": core.Selection(
        filter_variable="var_1",
        sign=core.SelectionSign.NOT_EQUAL_TO,
        union=core.UnionSign.NEGATIVE,
        filter_values=["val_1"]
    ),
    "&var with spaces=value with spaces": core.Selection(
        filter_variable="var with spaces",
        sign=core.SelectionSign.EQUAL_TO,
        union=core.UnionSign.NEGATIVE,
        filter_values=["value with spaces"]
    ),
    "|var=[value1,value2,value3]": core.Selection(
        filter_variable="var",
        sign=core.SelectionSign.EQUAL_TO,
        union=core.UnionSign.POSITIVE,
        filter_values=["value1", "value2", "value3"]
    ),
    "&var!=[value1,value2 with spaces,value3]": core.Selection(
        filter_variable="var",
        sign=core.SelectionSign.NOT_EQUAL_TO,
        union=core.UnionSign.NEGATIVE,
        filter_values=["value1", "value2 with spaces", "value3"]
    ),
}

def test_consume():
    """Tests that consume does the things it needs to do"""
    for key, value in CONSUME_RESULTS.items():
        selection, remainder = core.Selection.consume(key)
        assert selection == value
        assert remainder is None


def test_consume_all():
    query = "?var_1=val_1"
    results = [core.Selection(
        filter_variable="var_1",
        sign=core.SelectionSign.EQUAL_TO,
        union=core.UnionSign.POSITIVE,
        filter_values=["val_1"]
    )]

    for key, value in CONSUME_RESULTS.items():
        query += key
        results.append(value)

    assert core.Selection.consume_all(query) == tuple(results)


def test_metapath_init():
    query = "/path/to/file@some_selection_var?var_1=val_1"
    results = [core.Selection(
        filter_variable="var_1",
        sign=core.SelectionSign.EQUAL_TO,
        union=core.UnionSign.POSITIVE,
        filter_values=["val_1"]
    )]

    for key, value in CONSUME_RESULTS.items():
        query += key
        results.append(value)

    constructed_path = core.MetaPath(query)

    assert constructed_path.file == Path("/path/to/file")
    assert constructed_path.original == query
    assert constructed_path.selection_var == "some_selection_var"
    assert constructed_path.selections == tuple(results)


def test_exec():
    assert core.exec(["echo", "hello\nthere. How\nare you??"]) == "hello\nthere. How\nare you??"


def test_xsv_select(test_matrix_data):
    assert core.xsv_select(
        test_matrix_data,
        var="col3",
    ) == ["alpha", "beta", "alpha", "beta", "alpha", "beta"]

    assert core.xsv_select(
        test_matrix_data,
        var="col1",
    ) == ["a", "b", "c", "d", "e", "f"]

def test_tsv_xsv_select(test_tsv_data):
    assert core.xsv_select(
        test_tsv_data,
        var="col3",
        delim="\t"
    ) == ["alpha", "beta", "alpha", "beta", "alpha", "beta"]

    assert core.xsv_select(
        test_tsv_data,
        var="col1",
        delim="\t"
    ) == ["a", "b", "c", "d", "e", "f"]


def test_get_headers(test_matrix_data):
    assert core.get_headers(test_matrix_data) == ["id", "col1", "col2", "col3", "col4"]

def test_tsv_get_headers(test_tsv_data):
    assert core.get_headers(test_tsv_data, delimiter="\t") == ["id", "col1", "col2", "col3", "col4"]


def test_indexes_of():
    assert core.indexes_of(list("abcdef"), list("acf")) == [0, 2, 5]


def test_invert_index():
    assert core.invert_index(len(list("abcdef")), [0, 2, 5]) == [1, 3, 4]
