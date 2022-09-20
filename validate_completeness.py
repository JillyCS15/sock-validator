import argparse
import pandas as pd

from pyshacl import validate
from rdflib import Graph, URIRef, BNode, Literal, Namespace

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

def construct_data_graph(data, data_prop, entity_class):
    # convert data into data graph
    data_graph = Graph()

    # add default namespaces
    dbo_prefix = Namespace("http://dbpedia.org/ontology/")
    wd_prefix = Namespace("http://www.wikidata.org/entity/")
    data_graph.bind("dbo", dbo_prefix)
    data_graph.bind("wd", wd_prefix)

    # add instance relation for all entities
    # only used for checking with target for a certain class
    # if not, just skip it
    for _, row in data.iterrows():
        s = URIRef(row['entity.value'])
        p = URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
        o = URIRef(entity_class)
        data_graph.add((s, p, o))

    # add node-property relation for all entities
    for _, row in data_prop.iterrows():
        s = URIRef(row['s.value'])
        p = URIRef(row['p.value'])
        if row['o.type'] == 'literal':
            if row['o.xml:lang'] == 'not specified':
                o = o = Literal(row['o.value'])
            else:
                o = Literal(row['o.value'], lang=row['o.xml:lang'])
        elif row['o.type'] == 'typed-literal':
            o = Literal(row['o.value'], datatype=row['o.datatype'])
        else:
            o = URIRef(row['o.value'])
        data_graph.add((s, p, o))

    return data_graph

def construct_shapes_graph(shapes_file):
    # load shapes graph
    shapes_graph = Graph()
    shapes_graph.parse(shapes_file)

    return shapes_graph

if __name__ == "__main__": 
    parser = argparse.ArgumentParser(allow_abbrev=False,
                                        description="Arguments for completeness validation process")
    required = parser.add_argument_group('required arguments')

    required.add_argument("--data_file", type=str, required=True,
                            help="A file path of data file in csv format")
    required.add_argument("--data_prop_file", type=str, required=True,
                            help="A file path of data along with the properties in csv format")
    required.add_argument("--class_uri", type=str, required=True,
                            help="An URI of target class")
    required.add_argument("--shapes_file", type=str, required=True,
                            help="A file path of shapes graph in ttl format")
    required.add_argument("--prop_list", type=str, required=True, nargs="+",
                            help="A list of property to be check for each entity")

    args = parser.parse_args()
    data = pd.read_csv(args.data_file)
    data_prop = pd.read_csv(args.data_prop_file)
    class_uri = args.class_uri
    shapes_file = args.shapes_file
    prop_list = args.prop_list

    # handle NaN values in language attribute
    if 'o.xml:lang' in data_prop.columns.tolist():
        data_prop[['o.xml:lang']] = data_prop[['o.xml:lang']].fillna('not specified')

    # create data graph and shapes graph
    print("Constructing data graph ...")
    data_graph = construct_data_graph(data, data_prop, class_uri)
    print("Constructing shapes graph ...")
    shapes_graph = construct_shapes_graph(shapes_file)

    # validate the data graph
    print("Validating the completeness ...")
    conforms, report_graph, report_text = validate_graph(shapes_graph, data_graph)

    # generate completeness validation report
    print("Generating the completeness validation report ...")
    validation = create_report_validation(data, "entity.value", report_graph, prop_list)
    validation.to_csv("validation_report.csv", index=False)

    print("Successfully validated the data completeness")
