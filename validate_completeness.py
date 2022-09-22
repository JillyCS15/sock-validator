import argparse
import pandas as pd

from pyshacl import validate
from rdflib import Graph, URIRef


def validate_graph(shapes_graph, data_graph, is_advanced=False):
    """
    Validate the data graph over the shapes graph with the SHACL engine provided by PySHACL.
    
    Parameters
    ----------
    shapes_graph : Graph
        The shapes graph containing all the constraints
    data_graph : Graph
        The data graph containing all the instances to be validated along with their property values
    is_advanced : boolean, optional
        ...

    Returns
    -------
    (bool, Graph, str)
        value of conformation, validation report in the shape of a graph, and
        validation report in the shape of a text
    """
    result = validate(
        data_graph = data_graph,
        shacl_graph = shapes_graph,
        advanced = is_advanced,
        serialize_report_graph='ttl',
        )
    
    return result


def create_report_validation(df, use_col, report_graph, prop_list):
    report = Graph()
    report.parse(data=report_graph)

    # get the required properties
    # TODO

    # list all incompleteness
    list_incomplete = []

    for prop in prop_list:
        report_query = f"""
PREFIX dbo: <http://dbpedia.org/ontology/>
SELECT ?focusNode
WHERE {{
[] <http://www.w3.org/ns/shacl#result> ?id .
?id <http://www.w3.org/ns/shacl#focusNode> ?focusNode ;
    <http://www.w3.org/ns/shacl#resultPath> {prop} .
}}
"""
        res = report.query(report_query)

        list_entities = []
        for row in res:
            list_entities.append([str(row.focusNode), 0])

        list_incomplete.append(list_entities)

    # convert to dict of incompleteness
    validation = df[[use_col]]
    incomplete_dict = dict()
    for idx, prop in enumerate(prop_list):
        incomplete_dict[f"df_incomplete_{prop}"] = pd.DataFrame(list_incomplete[idx], columns=[use_col, prop])

    # merge the information
    for key in incomplete_dict.keys():
        validation = pd.merge(validation, incomplete_dict[key], on=use_col, how='left').fillna(1)

    validation['complete_all'] = validation.iloc[:,1:].sum(axis=1)/len(prop_list)
    return validation

def construct_graph(graph_file):
    # load graph
    graph = Graph()
    graph.parse(graph_file)

    return graph


if __name__ == "__main__": 
    parser = argparse.ArgumentParser(allow_abbrev=False,
                                        description="Arguments for completeness validation process")
    required = parser.add_argument_group('required arguments')

    required.add_argument("--data_file", type=str, required=True,
                            help="A file path of data file in csv format")
    required.add_argument("--data_prop_file", type=str, required=True,
                            help="A file path of data along with the properties in csv format")
    required.add_argument("--data_graph", type=str, required=True,
                            help="A file path of data graph in ttl format")
    required.add_argument("--shapes_graph", type=str, required=True,
                            help="A file path of shapes graph in ttl format")

    args = parser.parse_args()
    data = pd.read_csv(args.data_file)
    data_prop = pd.read_csv(args.data_prop_file)
    data_graph_file = args.data_graph
    shapes_graph_file = args.shapes_graph

    # handle NaN values in language attribute
    if 'o.xml:lang' in data_prop.columns.tolist():
        data_prop[['o.xml:lang']] = data_prop[['o.xml:lang']].fillna('not specified')

    # create data graph and shapes graph
    print("Constructing data graph ...")
    data_graph = construct_graph(data_graph_file)
    print("Constructing shapes graph ...")
    shapes_graph = construct_graph(shapes_graph_file)

    # get all the required properties
    prop = set()
    for s, p, o in shapes_graph:
        if p == URIRef('http://www.w3.org/ns/shacl#path'):
            prop.add(o.n3())
    prop_list = list(prop)

    # validate the data graph
    print("Validating the completeness ...")
    conforms, report_graph, report_text = validate_graph(shapes_graph, data_graph)

    # generate completeness validation report
    print("Generating the completeness validation report ...")
    validation = create_report_validation(data, "entity.value", report_graph, prop_list)
    validation.to_csv("validation_report.csv", index=False)

    print("Successfully validated the data completeness")
