# Table of Contents
1. [Overview](#overview)
2. [Motivation](#motivation)
3. [Functions](#functions)
4. [How to Setup](#how-to-setup)
5. [Demonstration](#demonstration)
6. [Contributors](#contributors)

# Overview

<p align="center">
    <img src="./readme-images/logo.jpg" alt="drawing" width="75%"/>
</p>

SoCK Library is a library to help user getting information about completeness of knowledge graph data. This library was developed with Python containing functions that can be used in the process of validating the completeness of the knowledge graph data. The functions available in this library are data collection, completeness pattern instantiation, data validation, and data visualization. Users are expected to be familiar with using Python to use this library properly.

The SoCK library reuses some of the existing Python libraries as **requirements**, such as:
- [RDFLib](https://rdflib.readthedocs.io/)
- [SPARQLWrapper](https://sparqlwrapper.readthedocs.io/)
- [PySHACL](https://pypi.org/project/pyshacl/)
- [Pandas](https://pandas.pydata.org/)
- [Plotly](https://plotly.com/python/)

# Motivation

SoCK Validator is part of the SoCK Framework project and part of our WOP 2022 paper entitled "SoCK: SHACL on Completeness Knowledge". This project exists because of the rapid development of knowledge graphs. However, it is not supported by a good data quality, especially in terms of completeness. Therefore, the SoCK framework was developed as a pattern-oriented framework to support the creation and validation about completeness in KGs. All the developed patterns and their instantiations can be accessed <a href="https://sock.cs.ui.ac.id" target="_blank"><b>here</b></a>. Happy exploring!

# Functions

Here, the user has two options to use this library with **Python file** that run in command line or **Python Notebook file**.

If the user chooses the Python file, there are three files that can be executed.
- ```prepare_data.py```, generates all the data to be validated.
- ```generate_shape.py```, generates a shapes graph which contains a set of constraints that data should be conformed.
- ```validate_completeness.py```, performs a validation process and creates a report in csv file.

On the other side, if the user chooses the Python Notebook file, there are several functions to perform completeness pattern instatiation and completeness validation.

- ```query_sparql```, performs query on a SPARQL endpoint.
- ```get_data_prop```, gets all the required properties for a validation process.
- ```construct_node_shape```, build a node shape.
- ```construct_property_shape```, build a property shape.
- ```construct_shapes_graph```, merge a node shape and a property shape to be a shapes graph as an instance of completeness pattern.
- ```build_data_graph```, constructs a data graph from all the collected data.
- ```validate_graph```, performs a SHACL validation based on a data graph and a shapes graph.
- ```create_report_validation```, converts validation report from a graph to a form of table.
- ```create_completeness_info_viz```, generates a visualization from table of validation report.

All the functions above are generally used consecutively. We prepare a demo to use this library with all those functions on [this section](#code-example).

# How to Setup

1. Clone this repository
    ```cmd
    > git clone https://github.com/JillyCS15/sock-validator.git
    ```

2. If you choose Python Notebook file (.ipynb), then just open ```SoCK_Library.ipynb```. If you choose Python file (.py), you have to create a virtual environment at first and install all the module dependencies. Execute these commands below on the command line.

    ```cmd
    # create a virtual environment
    > python -m venv -env

    # get into the virtual environment
    > env\Script\activate

    # install all the module dependencies
    > pip install -r requirements.txt
    ```

# Demonstration

**Example Use Case**

Given a user wants to check each instance of class ```dbo:Country``` in DBpedia has a label and description property. Then, he finds out the properties he should check out, that are ```rdfs:label``` for a label property and ```rdfs:comment``` for a description property they used.

**Using Python File**

1. First thing first, we have to collect all the data and their corresponding property values. Assume you have created a file containing a query in SPARQL syntax named ```query.txt```. Then, we execute ```prepare_data.py``` along with the required arguments, such as file containing the SPARQL query for data collection, SPARQL endpoint where the SPARQL query executed, URI of entity's class, and a list of required properties. The code we execute should be like this below. After the execution, we get the data in a type of graph called **data graph** stored in the TTL file named ```data_graph.ttl```.

    ```
    > python prepare_data.py --query_file query.txt --sparql_endpoint http://dbpedia.org/sparql --class_uri http://dbpedia.org/ontology/Country --prop_list rdfs:label rdfs:comment
    ```

2. Next, we should create a shapes graph containing all the constraints for the data graph. We can check on the SoCK webapp [here](https://sock.cs.ui.ac.id/pattern/) which provide all the type of completeness patterns. Based on the use case, we choose a label and description completeness pattern. Here is the instantiation of its pattern using a manual approach. This instantiation then called as a shapes graph. The shapes graph then stored in the TTL file named ```shapes_graph.ttl```.

    ```
    # prefixes

    ex:CountryShape
    a sh:NodeShape;
    sh:targetClass dbo:Country;
    sh:property [ a sh:PropertyShape;
        sh:path rdfs:label;
        sh:minCount 1 ];
    sh:property [ a sh:PropertyShape;
        sh:path rdfs:comment;
        sh:minCount 1 ].
    ```

3. The last step, we are ready for the completeness validation. We execute ```validate_completeness.py``` along with the required arguments, such as data & data with the property values (in csv format), data graph, shapes graph, and list of properties to be checked.

    ```
    > python validate_completeness.py --data_file data.csv --data_prop_file data_prop.csv --data_graph data_graph.ttl --shapes_graph shapes_graph.ttl --prop_list rdfs:label rdfs:comment
    ```

4. The result is now we have a completeness validation report for each entity in a csv file named ```validation_report.csv```

**Using Python Notebook File**

1. First of all, we have to prepare a Python file to run all the codes. I recommend to use a Python Notebook file.

2. Create an instance of a completeness pattern from [here](https://sock.cs.ui.ac.id/pattern/). Based on the use case, we choose a label and description completeness pattern. Here is the instantiation of its pattern using a manual approach.
    ```
    # prefixes

    ex:CountryShape
    a sh:NodeShape;
    sh:targetClass dbo:Country;
    sh:property [ a sh:PropertyShape;
        sh:path rdfs:label;
        sh:minCount 1 ];
    sh:property [ a sh:PropertyShape;
        sh:path rdfs:comment;
        sh:minCount 1 ].
    ```

3. That instance is used to validate the knowledge graph data. So, now we have to get the data using the code below. Here we limit the result up to 1000 first data.
    ```python
    # get all data to be validated
    query = """
    SELECT DISTINCT ?entity
    WHERE {
        ?entity a dbo:Country .
    }
    LIMIT 1000
    """

    data = query_sparql(query, "http://dbpedia.org/sparql")


    # get all the property values
    data['entity'] = data['entity.value'].apply(lambda x: f"<{x}>")

    dbpedia_endpoint = "http://dbpedia.org/sparql"
    prop_list = ['rdfs:label', 'rdfs:comment']

    data_prop = get_data_prop(data, prop_list, 50, dbpedia_endpoint)
    ```

4. After we get all the data, we have to build a data graph and a shapes graph. Let's say that the pattern instance we use is saved on ```./LDC-Country.ttl```.
    ```python
    # build data graph
    data_graph = build_data_graph(data, data_prop)

    # build shapes graph from the instantiation
    shapes_graph = build_shapes_graph("./LDC-Country.ttl")
    ```

5. Having the data graph and shapes graph, We are ready to run a validation process as a code written below.
    ```python
    conforms, report_graph, report_text = validate_graph(shapes_graph, data_graph)
    ```

6. Then, we create a validation report in a form of table. We use ```create_report_validation``` to convert a validation report from a graph to a table form.
    ```python
    prop_list = ['rdfs:label', 'rdfs:comment']

    validation = create_report_validation(data, "entity.value", report_graph, prop_list)
    ```

7. Lastly, we visualize the report to simplify the analysis and understanding process.
    ```python
    create_completeness_info_viz(
        validation,
        prop_list,
        'Label and Description Completeness Validation of ...')
    ```
    <p align="center">
        <img src="./readme-images/ldc-country.png" alt="drawing" width="75%"/>
    </p>

# Contributors

Thanks for all these great people from the **Faculty of Computer Science, Universitas Indonesia**, to contribute in this project:
- [Muhammad Jilham Luthfi](mailto:jilham.luthfi15@gmail.com)
- [Fariz Darari](mailto:fariz@ui.ac.id)
- [Amanda Carrisa Ashardian](mailto:amanda.carrisa@ui.ac.id)
