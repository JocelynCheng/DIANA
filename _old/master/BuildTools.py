import logging
import os
import subprocess

module_paths = [
    '.',
    'DianaConnect',
    'DianaFE',
    'DixelKit',
    'DianaStack',
    'GUIDMint',
    'DianaSplunk/rad_rx'
]

def consolidate_reqs():
    s = set()
    for r in module_paths:
        fn = os.path.join('.', r, 'requirements.txt')
        if os.path.exists(fn):
            with open(fn, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if not line.endswith('\n'):
                        line = line + '\n'
                    s.add(line)
    with open('requirements.txt', 'w') as f:
        ss = "{}".format(''.join(s))
        logging.debug(ss)
        f.write(ss)


def readme2rst():
    """
    External package requirement `pandoc`
    """
    for r in module_paths:

        cmd = ['/usr/local/bin/pandoc',
                         '--from=markdown',
                         '--to=rst',
                         '--output=./{}/README.rst'.format(r),
                         './{}/README.md'.format(r)]
        logging.debug(" ".join(cmd))
        subprocess.call(cmd)

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    readme2rst()
    consolidate_reqs()