#-------------------------------------------------------------------------------
# bindlibrary.py
#
# bindlibrary
#
#
# Copyright (C) 2015, Ryosuke Fukatani
# License: Apache 2.0
#-------------------------------------------------------------------------------

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) )

import pyverilog.utils.version
import pyverilog.utils.util as util
from pyverilog.dataflow.dataflow import *

cache = {}
class BindLibrary(object):
    def __init__(self, binddict, terms):
        def make_scope_dict(terms):
            """ [FUNCTIONS] for getScopeChaindict
            make {string: ScopeChain, ...} from binddict
            """
            return_dict = {}
            for scope in terms.keys():
                return_dict[str(scope)] = scope
            return return_dict

        self._binddict = binddict
        self._terms = terms
        self.scope_dict = make_scope_dict(terms)

    def dfx_memoize(f):
        def helper(self, target_tree, tree_list, term_lsb, bit, dftype):
            if dftype == pyverilog.dataflow.dataflow.DFTerminal:
                if (target_tree,term_lsb,bit) not in cache:
                    cache[(target_tree,term_lsb,bit)] = f(self, target_tree, set([]), term_lsb, bit, dftype)
                return tree_list.union(cache[(target_tree,term_lsb,bit)])
            else:
                return f(self, target_tree, tree_list,term_lsb,bit,dftype)
        return helper

    #@dfx_memoize
    def extract_all_dfxxx(self, target_tree, tree_list, term_lsb, bit, dftype):
        """[FUNCTIONS]
        type
        target_tree:DF***
        tree_list:{(type, DF***, bit),(type, DF***, bit),...}
        term_lsb:integar
        bit: signal bit pointer
        dftype: DFOperator or DFIntConst or ,...
        """
        if dftype == pyverilog.dataflow.dataflow.DFTerminal and isinstance(target_tree, pyverilog.dataflow.dataflow.DFTerminal):
            target_scope = self.get_scope(target_tree)
            if target_scope in self._binddict.keys():
                target_bind, target_term_lsb = self.get_next_bind(target_scope, bit)
                if not target_bind.isCombination():
                    tree_list.add((target_tree, bit))
            else:
                tree_list.add((target_tree, bit))
        else:
            if isinstance(target_tree, dftype):
                tree_list.add((target_tree, bit))

        if hasattr(target_tree, "nextnodes"):
            if isinstance(target_tree, pyverilog.dataflow.dataflow.DFConcat):
                now_max_bit = term_lsb
                now_min_bit = term_lsb
                for nextnode in reversed(target_tree.nextnodes):
                    now_max_bit = now_min_bit + self.get_bit_width_from_tree(nextnode) - 1
                    if now_min_bit <= bit <= now_max_bit:
                        tree_list = self.extract_all_dfxxx(nextnode, tree_list, 0, bit - now_min_bit, dftype)
                        break
                    now_min_bit = now_max_bit + 1
            else:
                for nextnode in target_tree.nextnodes:
                    if isinstance(target_tree, pyverilog.dataflow.dataflow.DFBranch) and nextnode == target_tree.condnode:
                        tree_list = self.extract_all_dfxxx(nextnode,tree_list, term_lsb, 0, dftype)
                    #elif isinstance(target_tree, pyverilog.dataflow.dataflow.DFOperator) and target_tree.is_alith:
                    #    raise verror.ImplementationError('not supported in regmap analyzer.')
                    else:
                        tree_list = self.extract_all_dfxxx(nextnode,tree_list, term_lsb, bit, dftype)
        elif isinstance(target_tree, pyverilog.dataflow.dataflow.DFBranch):
            tree_list = self.extract_all_dfxxx(target_tree.condnode,tree_list, term_lsb, 0, dftype)
            tree_list = self.extract_all_dfxxx(target_tree.truenode,tree_list, term_lsb, bit, dftype)
            tree_list = self.extract_all_dfxxx(target_tree.falsenode,tree_list, term_lsb, bit, dftype)
        elif isinstance(target_tree, pyverilog.dataflow.dataflow.DFTerminal):
            target_scope = self.get_scope(target_tree)
            if target_scope in self._binddict.keys():
                target_bind, target_term_lsb = self.get_next_bind(target_scope, bit)
                if target_bind.isCombination():
                    tree_list = self.extract_all_dfxxx(target_bind.tree, tree_list, target_term_lsb, bit, dftype)
        elif isinstance(target_tree, pyverilog.dataflow.dataflow.DFPartselect):
            var_node = target_tree.var
            ref_bit = self.eval_value(target_tree.lsb) + bit - term_lsb
            if isinstance(var_node, pyverilog.dataflow.dataflow.DFConcat) or isinstance(var_node, pyverilog.dataflow.dataflow.DFPartselect):
                ref_term_lsb = 0
            elif isinstance(var_node, pyverilog.dataflow.dataflow.DFIntConst):
                return tree_list
            else:
                var_scope = self.get_scope(var_node)
                ref_term_lsb = self.get_next_bind(var_scope, ref_bit)[1]
            tree_list = self.extract_all_dfxxx(var_node,tree_list, ref_term_lsb, ref_bit, dftype)
        return tree_list

    def delete_cache(self):
        global cache
        cache = {}

    def gnb_memoize(f):
        def helper(x,y,z):
            if (x,y,z) not in cache:
               cache[(x,y,z)] = f(x,y,z)
            return cache[(x,y,z)]
        return helper

    @gnb_memoize
    def get_next_bind(self, scope, bit):
        """[FUNCTIONS] get root bind.(mainly use at 'Rename' terminal.)
        """
        if scope in self._binddict.keys():
            target_binds = self._binddict[scope]
            target_bind_index = self.get_bind_index(target_binds, bit, self._terms[scope])
            target_bind = target_binds[target_bind_index]
            return target_bind, self.get_bind_lsb(target_bind)
        else:
            return None, self._terms[scope].lsb

    def get_bind_index(self, binds=None, bit=None, term=None, scope=None):
        """[FUNCTIONS] get bind index in that target bit exists.
        """
        if 'Rename' in term.termtype:
            return 0
        else:
            if scope is not None:
                binds = self._binddict[scope]
                term = self._terms[scope]
            for index,bind in enumerate(binds):
                if bind.lsb is None:#need for assign sentente ex. assign LED[7:0] = enable ? 'hff : 0;
                    return 0
                if self.get_bind_lsb(bind) <= bit <= self.get_bind_msb(bind):
                    return index
            else:
                raise IRREGAL_CODE_FORM("unexpected bind @"+binds[0].tostr())


    def get_bit_width_from_tree(self, tree):
        onebit_comb = ('Ulnot','Unot','Eq', 'Ne','Lor','Land','Unand','Uor','Unor','Uxor','Uxnor')
        if isinstance(tree, pyverilog.dataflow.dataflow.DFTerminal):
            term = self._terms[self.get_scope(tree)]
            return self.eval_value(term.msb)  + 1
        elif isinstance(tree, pyverilog.dataflow.dataflow.DFPartselect):
            return self.eval_value(tree.msb) - self.eval_value(tree.lsb) + 1
        elif isinstance(tree, pyverilog.dataflow.dataflow.DFOperator):
            if tree.operator in onebit_comb:
                return 1
            else:
                each_sizes = (self.get_bit_width_from_tree(nextnode) for nextnode in tree.nextnodes)
                return min(each_sizes)
        elif isinstance(tree, pyverilog.dataflow.dataflow.DFIntConst):
            return tree.width()
        elif isinstance(tree, pyverilog.dataflow.dataflow.DFConcat):
            return sum([self.get_bit_width_from_tree(nextnode) for nextnode in tree.nextnodes])
        else:
            raise IRREGAL_CODE_FORM("unexpected concat node")

    def walk_reg_each_bit(self):
        for tk, tv in sorted(self._terms.items(), key=lambda x:len(x[0])):
            if tk in self._binddict.keys():
                for bvi in self._binddict[tk]:#process for each always block
                    bind_lsb = self.get_bind_lsb(bvi)
                    bind_msb = self.get_bind_msb(bvi)
                    for bit in range(bind_lsb, bind_msb + 1):
                        yield tv, tk, bvi, bit, bind_lsb

    def get_bind_lsb(self, bind):
        if bind.lsb:
            return bind.lsb.value
        else:
            return 0

    def get_bind_msb(self, bind):
        if bind.msb:
            return bind.msb.value
        else:
            return 0

    def eval_value(self, tree):
        if isinstance(tree, pyverilog.dataflow.dataflow.DFOperator):
            for nextnode in self.nextnodes:
                assert(isinstance(nextnode, pyverilog.dataflow.dataflow.DFEvalValue)
                    or isinstance(nextnode, pyverilog.dataflow.dataflow.DFIntConst)
                    or isinstance(nextnode, pyverilog.dataflow.dataflow.DFOperator)
                    or isinstance(nextnode, pyverilog.dataflow.dataflow.DFTerminal))
            if self.operator == 'Plus':
                return self.eval_value(nextnodes[0]) + self.eval_value(nextnodes[1])
            elif self.operator == 'Minus':
                return self.eval_value(nextnodes[0]) - self.eval_value(nextnodes[1])
            elif self.operator == 'Times':
                return self.eval_value(nextnodes[0]) * self.eval_value(nextnodes[1])
            else:#unimplemented
                raise Exception
        elif isinstance(tree, pyverilog.dataflow.dataflow.DFTerminal):
            if self.get_scope(scopedict) in binddict.keys():
                return binddict[self.get_scope(scopedict)][0].tree.eval()
            else:
                raise verror.ImplementationError()
        elif isinstance(tree, pyverilog.dataflow.dataflow.DFIntConst):
            return tree.eval()
        elif isinstance(tree, pyverilog.dataflow.dataflow.DFEvalValue):
            return tree.value

    def get_scope(self, tree):
        name = str(tree)
        if name in self.scope_dict.keys():
            return self.scope_dict[name]
        else:
            return None