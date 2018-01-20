import sys
import os
import re
import yaml

root_dir = sys.argv[1]
zuul_d_dir = root_dir + '/zuul.d'
zuul_dir = root_dir + '/zuul'

job_file_path = zuul_d_dir + '/jobs.yaml'

def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.load(f)

job_conf = load_yaml(job_file_path)

def list_roles(root_dir):
    roles_path = root_dir + '/roles'
    (_, dirnames, _) = next(os.walk(roles_path))
    return dirnames

def list_playbooks(root_dir):
    playbooks = []
    playbooks_path = root_dir + '/playbooks'
    yaml_ext_regexp = re.compile(r'.*\.yaml')
    for path, dirs, files in os.walk(playbooks_path):
        for f in files:
            if yaml_ext_regexp.match(f):
                playbook_file_stripped = f[:-5]
                playbook_name = os.path.relpath(os.path.join(path, playbook_file_stripped), playbooks_path)
                playbooks.append(playbook_name)
            else:
                print('Bad filename in playbooks:', path, f)
    return playbooks

def used_roles(root_dir, playbook_name):
    roles = []
    pb = load_yaml(os.path.join(root_dir + '/playbooks', playbook_name + '.yaml'))
    for play in pb:
        playroles = play.get('roles', [])
        for r in playroles:
            if type(r) == dict:
                roles.append(r['role'])
            else:
                roles.append(r)
    return roles

roles = list_roles(root_dir)
playbooks = list_playbooks(root_dir)
print('All roles in dir:', roles)
print('All playbooks:', playbooks)
print()
all_used_roles = set()

for pb in playbooks:
    all_used_roles.update(used_roles(root_dir, pb))

#print(all_used_roles)
print('Used but not existing roles:', all_used_roles.difference(roles))
print('Existing but not used roles:', set(roles).difference(all_used_roles))

jobs = {}

for item in job_conf:
    assert(type(item) == dict)
    assert(len(item) == 1)
    assert('job' in item)
    item = item['job']
    jobs[item['name']] = item

def dump_playbooks(start_indent, indent_spaces, playbooks, title, root_dir):
    if not playbooks or playbooks == [None]:
        print(title, 'EMPTY')
        return
    indent = start_indent
    print(title)
    for p in playbooks:
        print(' ' * indent + '*************', p)
        with open(root_dir + '/' + p + '.yaml', 'r') as playbook:
            for l in playbook.readlines():
                print(' ' * indent + '*', l, end='')
            #print(playbook.read())
        print(' ' * indent + '*************')
        print()
        indent += indent_spaces

def dump_job(name):
    pre_playbooks = []
    run_playbook = None
    post_playbooks = []
    
    look_job = name
    
    def always_list(obj):
        if type(obj) != list:
            return [obj]
        return obj
    inheritance = [] 
    while look_job is not None:
        inheritance.append(look_job)
        j = jobs[look_job]
        pre_playbooks = always_list(j.get('pre-run', [])) + pre_playbooks
        if run_playbook == None:
            run_playbook = j.get('run', None)
        post_playbooks = post_playbooks + always_list(j.get('post-run', []))
        look_job = j.get('parent', None)

    print('inheritance:', inheritance)
    print('pre', pre_playbooks)
    print('run', run_playbook)
    print('post', post_playbooks)

    start_indent = max(0, len(post_playbooks) - len(pre_playbooks))
    run_indent = max(len(post_playbooks), len(pre_playbooks))
    indent_spaces = 4
    start_indent *= indent_spaces
    run_indent *= indent_spaces
    i = 0
    dump_playbooks(start_indent, indent_spaces, pre_playbooks, 'PRE', root_dir)
    dump_playbooks(run_indent, indent_spaces, [run_playbook], 'RUN', root_dir)
    dump_playbooks(run_indent-indent_spaces, -indent_spaces, post_playbooks, 'POST', root_dir)

for name in jobs:
    print()
    print('Dumping job', name)
    dump_job(name)
