#! /usr/bin/python3
# -*- coding: utf-8 -*-

from utils import InputData, Graph, OutputGetter
from argparse import ArgumentParser


if __name__ == "__main__":
    parser = ArgumentParser(usage='solution.py [-h] data origin destination [--bags] [--return_flight] [--max_transfer] [--max_layover_time]\n'
                                'For a given flight data in a form of csv file, prints out a structured list of all flight combinations for a selected route between airports A -> B, sorted by the final price for the trip.')
    parser.add_argument("data", type=str, help="CSV file with input data.")
    parser.add_argument("origin", type=str, help="Origin airport.")
    parser.add_argument("destination", type=str, help="Destination airport.")
    parser.add_argument("--bags", default=0, type=int, help="Number of requested bags. (Optional)")
    parser.add_argument("--return_flight", default=False, type=bool, help="Is it a return flight? (Optional)")
    parser.add_argument("--max_transfer", default=None, type=int, help="Max number of allowed interchange airports. (Optional)")
    parser.add_argument("--max_layover_time", default=6, type=int, help="Max time in hours for one layover time. (Optional)")
    args = parser.parse_args()

    if not (args.data or args.origin or args.destination):
        parser.print_help(file=None)
        exit()

    # prepare the input data
    input_data = InputData(args.data)
    input_data.check_airports(args.origin, args.destination)
    input_data.filter_bags(args.bags)

    # find all paths
    graph = Graph(input_data.input_vals)
    paths = graph.find_paths(args.origin, args.destination, args.max_transfer, args.max_layover_time)

    if args.return_flight:
        return_paths = graph.find_paths(args.destination, args.origin, args.max_transfer, args.max_layover_time)
    else:
        return_paths = []

    # print the output
    output = OutputGetter(input_data.flights, paths, args.bags, return_paths)
    output.print_output()

