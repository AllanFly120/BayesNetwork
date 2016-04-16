import sys
import copy
from collections import OrderedDict
from decimal import *
# input_path = "./HW3_samples/sample07.txt"
# output_path = "./output.txt"
input_path = sys.argv[-1]
output_path = './output.txt'


class Query:
    def __init__(self, type, X, evidence):
        self.type = type
        self.X = X
        self.evidence = evidence

    def get_type(self):
        return copy.copy(self.type)

    def get_X(self):
        return copy.deepcopy(self.X)

    def get_evidence(self):
        return copy.deepcopy(self.evidence)

    def query_print(self):
        print(self.type + '(', self.X, ' | ', self.evidence, ')')


class NodeInfo:
    def __init__(self):
        self.name = ""
        self.parents = []
        self.cpt = {}
        self.is_decision = False

    def set_name(self, name):
        self.name = name

    def set_parents(self, parents):
        self.parents = parents

    def addto_cpt(self, input, possibility):
        self.cpt[input] = possibility

    def set_decision(self):
        self.is_decision = True

    def __str__(self):
        return self.name + ' | ' + str(self.parents) + '\r' + str(self.cpt)


class Initiator:
    def __init__(self, input_path):
        self.path = input_path

    def parse_input(self):
        fin = open(self.path, 'r')
        rtn = {}
        rtn['query_list'] = self.parse_query(fin)
        fin.seek(0)
        rtn['bn'] = self.parse_bn(fin)
        fin.seek(0)
        rtn['utility'] = self.parse_utility(fin)
        fin.close()
        return rtn

    def parse_query(self, fin):
        query_list = []
        # fin = open(self.path, 'r')
        query_flag = True
        for line in fin.readlines():
            if '******' in line:
                break
            query_list.append(self.parse_query_line(line))
        # fin.close()
        return query_list

    def parse_query_line(self, line):
        query_type = line[0:line.find('(')]
        inside_p = line[line.find('(') + 1: line.find(')')]
        if inside_p.find('|') > -1:
            query_X = get_dict(inside_p[0:inside_p.find('|')].strip())
            query_evidence = get_dict(inside_p[inside_p.find('|')+1 : len(inside_p)].strip())
        else:
            query_X = get_dict(inside_p.strip())
            query_evidence = OrderedDict()
        return Query(query_type, query_X, query_evidence)

    def parse_bn(self, fin):
        bn = OrderedDict()
        bn_flag = False
        node = NodeInfo()  #substantiate a node for the first node info
        # fin = open(self.path, 'r')
        for line in fin.readlines():
            line = line.strip()
            if '******' not in line and bn_flag is True:  #begin to parse the bn
                if '***' not in line:  #this is a node info
                    if line[0].isupper() is True:  #the line with node name info
                        if ' | ' in line: #has parents info
                            node.set_name(line[0 : line.find(' | ')])
                            node.set_parents(line[line.find(' | ')+3 : len(line)].split(' '))
                        else: #node info line without parents info
                            node.set_name(line.strip())
                    elif 'decision' in line:
                        node.set_decision()
                    else:  #cpt info
                        possiblity = float(line[0:line.find(' ')]) if ('+' in line or '-' in line) else float(line.strip())
                        input = line[line.find(' ')+1 : len(line)].replace(' ', '') if ('+' in line or '-' in line) else '_'
                        node.addto_cpt(input, possiblity)
                elif '***' in line:
                    bn[node.name] = node
                    node = NodeInfo()  #substantiate another new node
            elif '******' in line:
                bn_flag = not bn_flag  #we only need to parse the content after the first ******* and stop after the second
        if node.name is not "":  #the last node info before '******'
            bn[node.name] = node
        # fin.close()
        return bn

    def parse_utility(self, fin):
        # fin = open(self.path, 'r')
        util_flag = False
        util = NodeInfo()
        for line in fin.readlines():
            line = line.strip()
            if util_flag is True:
                score = int(line[0:line.find(' ')]) if ('+' in line or '-' in line) else int(line.strip())
                input = line[line.find(' ')+1 : len(line)].replace(' ', '') if ('+' in line or '-' in line) else '_'
                util.addto_cpt(input, score)
            elif 'utility' in line:
                util_flag = True
                util.set_name(line[0 : line.find(' | ')])
                util.set_parents(line[line.find(' | ')+3 : len(line)].split(' '))
        return util


class Get_P:
    def enumerate(self, query, bn):
        rtn = self.enumerate_ask(query.get_X(), query.get_evidence(), bn)
        return rtn
        pass

    def enumerate_ask(self, X, evidence, bn):
        query_space = self.query_space(X)
        for signs in query_space.keys(): #arrangement of '-' '+' in X
            if self.check_conflict_all(copy.deepcopy(evidence), X, signs) is False:
                # print('p: 0', X, evidence)
                query_space[signs] = 0.0
                continue
            e = self.extend_all(copy.deepcopy(evidence), X, signs)
            # print(e)
            bn_tmp = copy.deepcopy(bn)
            query_space[signs] = self.enumerate_all(bn_tmp, copy.deepcopy(e))
        # print(query_space)
        return self.normalize(X, query_space)

    def enumerate_all(self, vars, evidence):
        if len(vars) is 0:
            return 1.0
        first_node = vars.popitem(last=False)
        if first_node[0] in evidence.keys():  # first_node[0] is the vars first node's name
            if first_node[1].is_decision is True or evidence[first_node[0]] is '+':
                p = self.conditional_p(first_node[1], evidence)
                # print('p: ', p, first_node[0], evidence)
                return p * self.enumerate_all(copy.deepcopy(vars),copy.deepcopy(evidence))
            else:
                p = 1.0 - self.conditional_p(first_node[1], evidence)
                # print('p: ', p, first_node[0], evidence)
                return p * self.enumerate_all(copy.deepcopy(vars),copy.deepcopy(evidence))
        else:
            e_for_positive = copy.deepcopy(evidence)
            e_for_positive = self.extend(e_for_positive, first_node[0], '+')
            positive_first = self.conditional_p(first_node[1], evidence)
            # print('pos: ', positive_first, first_node[0], evidence)
            positive_first *= self.enumerate_all(copy.deepcopy(vars),e_for_positive)
            e_for_negative = copy.deepcopy(evidence)
            e_for_negative = self.extend(e_for_negative, first_node[0], '-')
            negative_first = (1.0 - self.conditional_p(first_node[1], evidence)) if first_node[1].is_decision is False else self.conditional_p(first_node[1], evidence)
            # print('neg: ', negative_first, first_node[0], evidence)
            negative_first *= self.enumerate_all(copy.deepcopy(vars),e_for_negative)
            # print (positive_first, negative_first)
            return positive_first + negative_first
        pass

    def query_space(self, x):
        length = len(x)
        path = ''
        i = length
        while i > 0:
            path += '-'
            i -= 1
        space = {}
        self.query_space_helper(length, space, path)
        # print space
        return space

    def query_space_helper(self, length, space, path):
        space[path] = ''
        if length > 0:
            self.query_space_helper(length - 1, space, path)
            tmp_list = list(path)
            tmp_list[length - 1] = '+'
            path = ''.join(tmp_list)
            self.query_space_helper(length - 1, space, path)

    def extend_all(self, evidence, X, signs):
        for i, node in enumerate(X.keys()):
            evidence[node] = signs[i]
        return evidence

    def extend(self, evidence, variable, sign):
        evidence[variable] = sign
        return evidence

    def normalize(self, query, query_space):
        sum = 0
        for possibility in query_space.values():
            sum += possibility
        if sum == 0.0:
            return 0.0
        goal = ''
        for key, value in query.iteritems():
            goal += value
        return query_space[goal] / sum

    def conditional_p(self, node, e):
        if node.is_decision is True:
            return 1.0
        if len(node.parents) is 0:
            return node.cpt['_']

        cpt_row = ''
        for parent in node.parents:
            cpt_row += e[parent]
        # print cpt_row
        return node.cpt[cpt_row]

    def check_conflict_all(self, evidence, X, signs): #check for the confliction between X and evidence, must be put before enumerate all()
        for i, X_item in enumerate(X.keys()):
            if X_item in evidence.keys() and not signs[i] == evidence[X_item]:
                return False
        return True

    def check_conflict(self, evidence, node_name, sign): #check for confliction before enumerate()
        if node_name in evidence.keys() and not evidence[node_name] == sign:
            return False
        return True
        pass


class Get_EU:
    def scores(self, query, bn, utility):
        s = utility.parents
        query_space = Get_P().query_space(s)
        for query_instance in query_space.keys():
            sub_query = self.form_p(query_instance, query, s)
            P_calculator = Get_P()
            sub_EU = P_calculator.enumerate(sub_query, bn)
            # print(sub_EU)
            sub_EU *= utility.cpt[query_instance]
            # print(sub_EU)
            query_space[query_instance] = sub_EU
            # sub_query.query_print()
        rtn = sum(query_space.values())
        return rtn

    def form_p(self, signs, query, util_nodes):
        util_nodes = copy.deepcopy(util_nodes)
        X = OrderedDict()
        for i, node in enumerate(util_nodes):
            X[node] = signs[i]
        evidence = query.get_X()
        for key, value in query.get_evidence().iteritems():
            evidence[key] = value
        return Query('P', X, evidence)


class Get_MEU:
    def maxmize(self, query, bn, utility):
        choices = query.get_X().keys()
        choice_space = Get_P().query_space(choices)
        for choice_match in choice_space.keys():
            new_query = self.get_MEU_query(copy.deepcopy(query), choice_match)
            # new_query.query_print()
            EU_calculator = Get_EU()
            choice_space[choice_match] = EU_calculator.scores(new_query, bn, utility)
        # print choice_space
        max_pair = ['', -99999]
        for item in choice_space.iteritems():
            if item[1] > max_pair[1]:
                max_pair = item
        # print max_pair
        return max_pair

    def get_MEU_query(self, query, signs):
        query.type = 'EU'
        for i, variable in enumerate(query.X.keys()):
            query.X[variable] = signs[i]
        return query


def get_dict(string):
    rtn = OrderedDict()
    string = string.strip()
    dict_arr = string.split(', ')
    for item in dict_arr:
        item = item.strip()
        if item.find('=') > -1:
            variable = item[0 : item.find(' = ')]
            value = item[item.find(' = ')+3 : len(item)]
            rtn[variable] = value
        else:
            rtn[item] = ''
    return rtn


def main():
    init = Initiator(input_path)
    input = init.parse_input()
    query_list = input['query_list']
    bn = input['bn']
    util = input['utility']
    output_str = ''
    for query in query_list:
        if query.get_type() == 'P':
            P_calculator = Get_P()
            rtn = P_calculator.enumerate(query, bn)
            result = str(Decimal(str(rtn)).quantize(Decimal('0.01')))
            output_str += (result + '\r\n')
        elif query.get_type() == 'EU':
            EU_calculator = Get_EU()
            rtn = EU_calculator.scores(query, bn, util)
            result = str(Decimal(str(rtn)).quantize(Decimal('1')))
            output_str += (result + '\r\n')
        elif query.get_type() == 'MEU':
            MEU_calculator = Get_MEU()
            max_pair = MEU_calculator.maxmize(query, bn, util)
            for char in list(max_pair[0]):
                output_str += (str(char) + ' ')
            result = str(Decimal(str(max_pair[1])).quantize(Decimal('1')))
            output_str += (result + '\r\n')

    fout = open(output_path, 'w')
    fout.write(output_str)
    fout.close()






if __name__ == "__main__":
    main()