## Some fixed data for pytest
import pytest
from pathlib import Path
import shutil


@pytest.fixture
def test_matrix_data(tmp_path: Path) -> Path:
    data = """id,col1,col2,col3,col4
id1,a,1,alpha,"some,text"
id2,b,2,beta,"more text"
id3,c,3,alpha,"incredible"
id4,d,1,beta,"wow"
id5,e,2,alpha,"magic"
id6,f,3,beta,"generically wow"
"""
    path = (tmp_path / "matrix_data")
    path.open("w+").write(data)
    yield path

    if path.parent.exists():
        shutil.rmtree(path.parent)


@pytest.fixture
def test_tsv_data(tmp_path) -> Path:
    data = """id\tcol1\tcol2\tcol3\tcol4
id1\ta\t1\talpha\t"some\ttext"
id2\tb\t2\tbeta\t"more text"
id3\tc\t3\talpha\t"incredible"
id4\td\t1\tbeta\t"wow"
id5\te\t2\talpha\t"magic"
id6\tf\t3\tbeta\t"generically wow"
"""
    path = (tmp_path / "tsv_data")
    path.open("w+").write(data)
    yield path

    if path.parent.exists():
        shutil.rmtree(path.parent)

@pytest.fixture
def test_selection_data(tmp_path) -> Path:
    data = """id1,id2,id3,id4,id5,id6
a,b,c,d,e,f
g,h,i,j,k,l
m,n,o,p,q,r
s,t,u,v,w,x
"""
    path = (tmp_path / "selection_data")
    path.open("w+").write(data)
    yield path

    if path.parent.exists():
        shutil.rmtree(path.parent)
