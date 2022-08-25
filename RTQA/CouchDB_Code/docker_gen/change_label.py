from struct import pack
import yaml
import sys
import os

changeset_path = sys.argv[1]
output_path = sys.argv[2]
changeset_files = os.listdir(changeset_path)

package_counts = dict()
progress = set()

output_files = os.listdir(output_path)
for cs in output_files:
    title = cs[0:cs.find("=")]
    if title not in progress:
        progress.add(title)


for cs in changeset_files:
    title = cs[0:cs.find("=")]
    if title in progress:
        cont

    f = open(changeset_path + cs, 'r')
    cs_dict = yaml.load(f.read(), Loader=yaml.Loader)
    f.close()
    cs_dict['label'] = cs_dict['label'][0:cs_dict['label'].find("=")]

    if not (cs_dict['label'] in package_counts):
        package_counts[cs_dict['label']] = 1
    else:
        if package_counts[cs_dict['label']] == 10:
            continue
        else:
            package_counts[cs_dict['label']] += 1

    f_res = open(output_path + cs, "w")
    f_res.write(yaml.dump(cs_dict))
    f_res.close()
