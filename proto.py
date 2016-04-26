"""
Proto output plugin
Idea similar to Tree plugin 
"""

import optparse
import sys
import re
import string

from pyang import plugin
from pyang import statements

yang_proto_maping ={"int8":"int32",
		    "int16":"int32",
		    "int32":"int32",
		    "int64":"int64",
		    "uint8":"uint32",
		    "uint16":"uint32",
		    "uint32":"uint32",
		    "uint64":"uint64",
		    
		    "binary":"bytes",
		    "bits":"bytes",
		    "bool":"bool",
		    "boolean":"bool",
		    "decimal64":"decimal64",
		    "enum":"enum",
		    "identityref":"enuminstance",
		    "instanceIdentifier":"ii",
		    "leafref":"string",
		    "string":"string",
		    "union":"string",
		    "container":"message",
		    "":"empty"}

def pyang_plugin_init():
    plugin.register_plugin(ProtoPlugin())

class ProtoPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['proto'] = self

    def emit(self, ctx, modules, fd):
        if ctx.opts.tree_path is not None:
            path = string.split(ctx.opts.tree_path, '/')
            if path[0] == '':
                path = path[1:]
        else:
            path = None
        emit_proto(ctx, modules, fd, None, path)

def print_help():
    print("""
This module will help is generating a .proto file from a yang file
""")

def emit_proto(ctx, modules, fd, depth, path):
    for module in modules:

	"""Print message"""
	chs = [ch for ch in module.i_children
               if ch.keyword in statements.data_definition_keywords]
        if path is not None and len(path) > 0:
            chs = [ch for ch in chs if ch.arg == path[0]]
            path = path[1:]

        if len(chs) > 0:
	    print_messages(chs, module, fd, ' ', path, 'data', depth)

        mods = [module]
        for i in module.search('include'):
            subm = ctx.get_module(i.arg)
            if subm is not None:
                mods.append(subm)
        for m in mods:
            for augment in m.search('augment'):
                if (hasattr(augment.i_target_node, 'i_module') and
                    augment.i_target_node.i_module not in modules + mods):
                    # this augment has not been printed; print it
                    fd.write("augment %s:\n" % augment.arg)
                    print_messages(augment.i_children, m, fd,
                                   ' ', path, 'augment', depth)

	
	"""Print RPCs"""
	rpcs = [ch for ch in module.i_children
                if ch.keyword == 'rpc']
	
	if path is not None:
            if len(path) > 0:
                rpcs = [rpc for rpc in rpcs if rpc.arg == path[0]]
                path = path[1:]
            else:
                rpcs = []
	
	enums = {}
	enum_names ={}
	if len(rpcs) > 0:
	    """Print enums"""
	    for ch in module.substmts:
		if ch.keyword == 'identity':
		    enum_names[ch.arg] = ch
		    basetype = ch.search_one('base')
		    if basetype:
			if basetype.arg not in enums:
			    enums[basetype.arg] = []
			enums[basetype.arg].append(ch)
	
	if len(rpcs) > 0:
	    if (module.keyword == 'module'):
		description = [] 
		for statement in module.substmts:
		    if statement.keyword == 'description':
			print_description(statement.arg, fd, 0)
		
		fd.write('service '+str(module.arg)+'{')
	    fd.write('\n') 

	    for rpc in rpcs:
		print_description(rpc.search_one('description').arg, fd, 1)
		fd.write('\t'+str(rpc.keyword)+" "+rpc.arg+'('+str(rpc.arg)+'Request) ('+str(rpc.arg)+'Response) {}')
		fd.write('\n')
	    fd.write('}\n\n')
	    print_enums(enums, enum_names, fd)
	    print_messages(rpcs, module, fd, ' ', path, 'rpc', depth)

	"""Print for notifications"""
        notifs = [ch for ch in module.i_children
                  if ch.keyword == 'notification']
        if path is not None:
            if len(path) > 0:
                notifs = [n for n in notifs if n.arg == path[0]]
                path = path[1:]
            else:
                notifs = []
        if len(notifs) > 0:
            fd.write("notifications:\n")
            print_messages(notifs, module, fd, ' ', path, 'notification', depth)

def print_description(desc, fd, level):
    description = desc.split('\n')
    fd.write('\t'*level+'/*\n')
    for line in description:
        fd.write('\t'*(level)+' * '+line+'\n')
    fd.write('\t'*(level)+' */\n')

def print_enums(enums, enum_names, fd):
    for key in enums:
	count = 0
	
	print_description(enum_names[key].search_one('description').arg, fd, 0)
	fd.write("enum "+key+" {\n")
	
	for member in enums[key]:
	    print_description(member.search_one('description').arg, fd, 1)
	    fd.write("\t"+member.arg+" = "+str(count)+"\n")
	    count += 1
	fd.write("}\n\n")

def print_messages(children, module, fd, prefix, path, mode, depth, width = 0):
    global yang_proto_maping 
    
    if len(children) == 0:
	return
    member_count = 0
    for child in children:
	member_count += 1
	""" If input or output print message if rpc dont print anything"""
	element_type = child.keyword
	element_name = child.arg

	if element_type == 'input' or element_type == 'output' or element_type == 'rpc':
	    
	    """We dont need to print empty message"""
	    if len(child.i_children) > 0:
		
		if element_type == 'input':
		    print_description(child.parent.search_one('description').arg,
		    fd, width - 1)
		    fd.write("message "+str(child.parent.arg)+"Request {\n")
		
		if element_type == 'output':
		    print_description(child.parent.search_one('description').arg,
		    fd, width - 1)
		    fd.write("message "+str(child.parent.arg)+"Response {\n")
	else:
	    if get_typename(child) in yang_proto_maping.keys():
		
		data_type = yang_proto_maping[get_typename(child)]
		
		if element_type == 'list':
		    fd.write("\t"*width+"message "+str(element_name)+" {\n")
		
		elif element_type == 'container':
		    print_description(child.parent.search_one('description').arg,
		    fd, width)
		    fd.write("\t"*width+"message "+str(element_name)+" {\n")

		elif element_type == 'leaf':
		    if data_type == 'enuminstance':
			data_type = child.substmts[0].substmts[0].arg
			print_description(child.search_one('description').arg, fd, width)
			fd.write("\t"*width+str(data_type)+" "+str(element_name)+" = "+str(member_count)+";\n")
		    
		    else:
			print_description(child.search_one('description').arg, fd, width)
			fd.write("\t"*width+str(data_type)+" "+str(element_name)+" = "+str(member_count)+";\n")
		
		elif element_type == 'leaf-list':
		    
		    if data_type == 'enuminstance':
			data_type = child.substmts[0].substmts[0].arg
			print_description(child.search_one('description').arg, fd, width)
			fd.write("\t"*width+"repeated "+str(data_type)+" "+str(element_name)+" = "+str(member_count)+";\n")
		    else:	
			fd.write("\t"*width,"repeated "+str(element_type)+" "+str(element_name)+" = "+str(member_count)+";\n")
		
		else:
		    fd.write(" "*width+str(data_type)+" "+str(element_name)+" "+element_type+"\n")
	    
	    else:
		""" Data type mapping isn't available"""
		
		data_type = get_typename(child)
		
		if element_type == 'leaf-list':
		    print_description(child.search_one('description').arg, fd, width)
		    fd.write("\t"*width+"repeated string "+str(element_name)+" = "+str(member_count)+";\n")
		
		elif element_type == 'leaf':
		    print_description(child.search_one('description').arg, fd, width)
		    fd.write("\t"*width+"string "+element_name+" = "+str(member_count)+";\n")
		
		else:
		    fd.write(" "*width+str(data_type)+" string "+str(element_name)+" "+str(element_type)+"\n")

	if 'i_children' in dir(child):
	    print_messages(child.i_children, module, fd, prefix, path, mode, depth, width+1)
	
	if get_typename(child) in yang_proto_maping.keys():
	    
	    if element_type == 'container':
		fd.write("\t"*width+"}\n")
	    
	    elif element_type == 'list':
		fd.write("\t"*width+"}\n")
		print_description(child.search_one('description').arg, fd, width)
		fd.write("\t"*width+"repeated "+element_name+" "+element_name+"-list"+" = "+str(member_count)+";\n")
	
	if element_type == 'input' or element_type == 'output':
	    if len(child.i_children) > 0:
		fd.write('}\n\n')


def get_typename(s):
    t = s.search_one('type')
    if t is not None:
        if t.arg == 'leafref':
            p = t.search_one('path')
            if p is not None:
                # Try to make the path as compact as possible.
                # Remove local prefixes, and only use prefix when
                # there is a module change in the path.
                target = []
                curprefix = s.i_module.i_prefix
                for name in p.arg.split('/'):
                    if name.find(":") == -1:
                        prefix = curprefix
                    else:
                        [prefix, name] = name.split(':', 1)
                    if prefix == curprefix:
                        target.append(name)
                    else:
                        target.append(prefix + ':' + name)
                        curprefix = prefix
                return "-> %s" % "/".join(target)
            else:
                return t.arg
        else:
            return t.arg
    else:
        return ''
