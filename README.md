# Metasplit
A program to split (very) large .csv files column-wise based on some other metadata file with minimal memory overhead.

## Installation
This needs the `xsv` binary in your PATH, since it uses it as a backend to do the heavy lifting. Install it from the [BurntSushi/xsv](https://github.com/BurntSushi/xsv) repository.

You need to have python 3.10 or later installed. Install metasplit with:
```
pip install git+https://github.com/MrHedmad/metasplit@main
```

Then you can use metasplit with the `metasplit` command.

## Usage
Use `metasplit --help` for a list of arguments. The argument should be self-explaining with the exception of the selection strings. I explain them here.

A selection string is a structured strings with this form:
```
|--------------------| |---------||------------ >>>
/path/to/metadata/file@id_variable?meta_var1=value&meta_var2=value ...
                      ^           ^               ^
```
The query has many parts:
- `/path/to/metadata/file`: The (full) path to the metadata file to use to select the columns of the input file with.
- `id_variable`: The name of the column in the metadata file that holds the ids of the columns in the input file. Must be preceded by an `@`.
- After these two parts, the rest of the string is made up by selections:
  - The first selection always starts with an `?`. This marks the beginning of the selection strings.
  - Every selection is of the form `variable` + `sign` + `value(s)`. The variable is the column to consider in the metadata. The value(s) are either one (`value`) or a list of (`[value1,value2,value3]`) of values to select the ids with. The sign might be either `=` or `!=` for the variable being equal to or not equal to the values, respectively.
  - Multiple selections may be chained together by starting new selection strings with either `&` or `|` for a logical AND or a logical OR with the previous selection.

You can pass multiple selection strings as input, even from different metadata files. Each selection from every metadata file will be summed together to subset the final data file.

### Examples
Some examples of query strings:
- `~/metadata.csv@gene_id?sample_type=tumor`: Read the `~/metadata.csv` file, and select column ids in the `gene_id` column where the column `sample_type` is equal to `tumor`.
- `~/metadata.csv@gene_id?type=[primary_tumor,metastasis]&study=tcga`: Similar to the previous example, select where `type` is either `primary_tumor` or `metastasis` AND the `study` is `tcga`.
- `~/metadata.csv@gene_id?study=tcga|selection=manually_selected`: select where `study` is equal to `tcga` OR the `selection` is `manually_selected`.
