## Some fixed data for pytest
import pytest
from pathlib import Path


@pytest.fixture
def test_matrix_data(tmpdir) -> Path:
    data = """id,col1,col2,col3,col4
id1,a,1,alpha,"some,text"
id2,b,2,beta,"more text"
id3,c,3,alpha,"incredible"
id4,d,1,beta,"wow"
id5,e,2,alpha,"magic"
id5,f,3,beta,"generically wow"
"""
    path = tmpdir.join("data.csv")
    path.write(data)
    return Path(path)
