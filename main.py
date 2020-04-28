import os
from aerate.aerate import Aerate

SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))

aerate = Aerate(os.path.join(SCRIPT_ROOT, "xml"))

item = aerate.index.find_member_by_name("vector_c")
aerate.adjuster.handle(item.node)
print(aerate.renderer.handle(item.node))

item = aerate.index.find_member_by_name("vector_at", module="access.h")
aerate.adjuster.handle(item.node)
print(aerate.renderer.handle(item.node))

item = aerate.index.find_member_by_name("vector_index", module="access.h")
aerate.adjuster.handle(item.node)
print(aerate.renderer.handle(item.node))

item = aerate.index.find_member_by_name("vector_get", module="access.h")
aerate.adjuster.handle(item.node)
print(aerate.renderer.handle(item.node))

item = aerate.index.find_member_by_name("vector_set", module="access.h")
aerate.adjuster.handle(item.node)
print(aerate.renderer.handle(item.node))

item = aerate.index.find_member_by_name("vector_tail", module="access.h")
aerate.adjuster.handle(item.node)
print(aerate.renderer.handle(item.node))

item = aerate.index.find_member_by_name("vector_insert_z", module="insert.h")
aerate.adjuster.handle(item.node)
print(aerate.renderer.handle(item.node))
