#! /usr/bin/python3
# -*- coding: utf-8 -*-

import csv
import os
import json
from itertools import compress
from datetime import datetime, timedelta
from collections import deque


class InputData():
    """ Class for loading the input file and performing some basic checks."""
    def __init__(self, infile):
        assert infile[-4:] == '.csv', 'Input file is not in CSV format'
        outfile = 'output.csv'
        # check and remove duplicities in input file
        flights = set()
        with open(infile, 'r') as in_file, open(outfile,'w') as out_file:
            for row in in_file:
                if row in flights: continue
                out_file.write(row)
        
        self.input_vals = dict() # input vals for graph
        self.flights = dict() # informations about flights
        self.columns = ['flight_no', 'origin', 'destination', 'departure', 'arrival', 'base_price', 'bag_price', 'bags_allowed']
        try:
            for col in self.columns:
                self.input_vals[col] = [row[col] for row in csv.DictReader(open(outfile))]
        except KeyError:
            raise KeyError(f'One or more columns have incorrect names. Column names should be {self.columns}')

        with open(outfile,'r') as out_file:
            reader = csv.DictReader(out_file)
            i=0
            for row in reader:
                self.flights[i] = row
                i += 1
        os.remove(outfile)

        # add flight id
        self.input_vals['id'] = list(range(len(self.input_vals['origin'])))
        self.columns.append('id')

        # change datatypes
        try:
            self.input_vals['departure'] = [datetime.strptime(i, '%Y-%m-%dT%H:%M:%S') for i in self.input_vals['departure']]
            self.input_vals['arrival'] = [datetime.strptime(i, '%Y-%m-%dT%H:%M:%S') for i in self.input_vals['arrival']]
            self.input_vals['bags_allowed'] = [int(i) for i in self.input_vals['bags_allowed']]
            self.input_vals['base_price'] = [float(i) for i in self.input_vals['base_price']] 
            self.input_vals['bag_price'] = [float(i) for i in self.input_vals['bag_price']] 
        except ValueError:
            raise ValueError('One or more input values in the CSV file have a wrong format. Please check the formats: \n \
                    departure: YYYY-mm-ddTHH:MM:SS \n \
                    origin: YYYY-mm-ddTHH:MM:SS \n \
                    bags_allowed: int \n \
                    base_price: float \n \
                    bag_price: float')
        self._check_no_time_travel()

    def _check_no_time_travel(self):
        """ Checks if all flights have later arrival than departure."""
        for departure, arrival in zip(self.input_vals['departure'], self.input_vals['arrival']):
            if departure > arrival:
                raise ValueError(f'The file with input values contains a flight with later departure ({departure}) than arrival ({arrival}). Please  check.')

    def check_airports(self, origin, destination):
        """ Checks if origin and destination airports are present in input data"""
        if origin not in set(self.input_vals['origin']):
            raise ValueError('Input value for the origin airport is not in input data')
        if destination not in set(self.input_vals['destination']):
            raise ValueError('Input value for the destination airport is not in input data')

    def filter_bags(self, min_bags):
        """ Filters input flights based on required number of bags"""
        if min_bags > max(self.input_vals['bags_allowed']):
            raise ValueError('None of the flights allow the requested number of bags.')
        
        allowed = [i >= min_bags for i in self.input_vals['bags_allowed']]
        for col in self.columns:
            self.input_vals[col] = list(compress(self.input_vals[col], allowed))


class Graph():
    """ Class for finding all paths from the origin to the destination airport."""
    def __init__(self, input_data):
        self.num_airports = len(set(input_data['origin']).union(set(input_data['destination'])))
        self.data = dict()
        for airport in set(input_data['origin']):
            self.data[airport] = []
        for o, d, t1, t2, id in zip(input_data['origin'], input_data['destination'], input_data['departure'], input_data['arrival'], input_data['id']):
            self.data[o].append([d, t1, t2, id])

    def _find_adepts(self, origin, time):
        """ Auxiliary function - finds possible interchange airports"""
        adepts = self.data[origin[0]]
        return [i for i in adepts if (origin[2] + timedelta(hours = 1)) <= i[1] <= (origin[2] + timedelta(hours = time))]

    def find_paths(self, origin, destination, max_transfer, max_layover_time):
        """ Finds all allowed paths from origin to destination based on entry conditions"""
        visited_airports = [origin]
        try:
            stack = deque(self.data[origin].copy())
        except KeyError:
            raise KeyError('There is no flight from the origin airport with the requested parameters.')
        paths = []
        path = []
        count = [len(stack)]
        if max_transfer is None:
            max_transfer = self.num_airports - 2

        while stack:
            node = stack.popleft()
            count[-1] -= 1
            if node[0] == destination:
                path.append(node[3])
                paths.append(path.copy())
                path.pop()              
            elif (node[0] not in visited_airports) and ((len(visited_airports) - 1) < max_transfer):
                adepts = self._find_adepts(node, max_layover_time)
                if adepts:
                    visited_airports.append(node[0])
                    stack.extendleft(adepts)
                    path.append(node[3])
                    count.append(len(adepts))
            if count[-1] == 0 and len(count) > 1:
                path.pop()
                count.pop()            
        return paths


class OutputGetter():
    """ Class for printing the output in requested format."""
    def __init__(self, flights, paths, bags, return_paths):
        self.flights = flights
        self.paths = paths
        self.bags = bags
        self.prices = self._get_prices(self.paths)
        self.travel_times = self._get_travel_times(self.paths)
        self.print_order = [i[0] for i in sorted(enumerate(self.prices), key=lambda x:x[1])]
        self.return_paths = return_paths

    def _get_prices(self, paths):
        """ Auxiliary function - computes price for each path and get order for printing output"""
        prices = []
        for path in paths:
            base_price = sum([float(self.flights[f]['base_price']) for f in path])
            bag_price = self.bags*sum([float(self.flights[f]['bag_price']) for f in path])
            prices.append(base_price+bag_price)
        return prices

    def _get_travel_times(self, paths):
        """ Auxiliary function - computes travel_time for each path"""
        travel_times = []
        for path in paths:
            start_time = datetime.strptime(self.flights[path[0]]['departure'], '%Y-%m-%dT%H:%M:%S')
            end_time = datetime.strptime(self.flights[path[-1]]['arrival'], '%Y-%m-%dT%H:%M:%S')
            travel_times.append(str(end_time - start_time))
        return travel_times

    def _get_output_for_one_path(self, path, name, price, travel_time):
        """ Auxiliary function - get a dictionary with the information for one path.
        :param path: path for which the output is to be created
        :param name: flights or return_flights
        :param price: price of the path
        :param travel_times: travel time of the path
        """
        output_for_one_path = dict()
        output_for_one_path[name] = [self.flights[f] for f in path]
        output_for_one_path['bags_allowed'] = min([int(self.flights[f]['bags_allowed']) for f in path])
        output_for_one_path['bags_count'] = self.bags
        output_for_one_path['destination'] = self.flights[path[-1]]['destination']
        output_for_one_path['origin'] = self.flights[path[0]]['origin']
        output_for_one_path['total_price'] = price
        output_for_one_path['travel_time'] = travel_time
        return output_for_one_path

    def print_output(self):
        """ Print structured list of all flight combinations sorted by final price for the trip"""
        print_out = []
        if self.return_paths:
            return_prices = self._get_prices(self.return_paths)
            return_travel_times = self._get_travel_times(self.return_paths)
            return_print_order = [i[0] for i in sorted(enumerate(return_prices), key=lambda x:x[1])]
        # write output paths in required order
        for i in self.print_order:
            output_for_one_path = self._get_output_for_one_path(self.paths[i], 'flights', self.prices[i], self.travel_times[i])
            print_out.append(output_for_one_path)
            
            if self.return_paths:
                return_out = []
                arrival = datetime.strptime(self.flights[self.paths[i][-1]]['arrival'], '%Y-%m-%dT%H:%M:%S')
                for j in return_print_order:
                    departure = datetime.strptime(self.flights[self.return_paths[j][0]]['departure'], '%Y-%m-%dT%H:%M:%S')
                    # find only return paths with departude at least one day after arrival
                    if (arrival + timedelta(hours = 24)) < departure:
                        output_for_one_return_path = self._get_output_for_one_path(self.return_paths[j], 'return_flights', return_prices[j], return_travel_times[j])
                        return_out.append(output_for_one_return_path)

                if return_out:
                    print_out.append(return_out)
                else:
                    # if there is no possible return path then delete also the original path
                    print_out.pop()

        print(json.dumps(print_out, indent = 4))