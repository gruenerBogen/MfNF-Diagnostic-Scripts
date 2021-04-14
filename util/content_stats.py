import re
import os


def extract_content(string, regex_string):
    """
    Find all <section> environments and return their content as string array.
    """
    gallery_regex = re.compile(regex_string, re.DOTALL)
    return [match.group(1) for match in gallery_regex.finditer(string)]


def find_content(pages, regex_string):
    content_dict = {}
    for page in pages:
        content = extract_content(pages[page], regex_string)
        if len(content) > 0:
            content_dict[page] = content
    return content_dict


def map_content(fn, content_dict):
    new_dict = {}
    for page in content_dict:
        new_dict[page] = [fn(content) for content in content_dict[page]]
    return new_dict


def basic_analysis(base_name, pages, regex_string):
    content_dict = find_content(pages, regex_string)
    content_pages = [(page, len(content_dict[page])) for page in content_dict]
    content_counter = sum([t for (_, t) in content_pages])

    print("Found {} content uses.".format(content_counter))

    os.makedirs("out", exist_ok=True)
    with open("out/{}_stats.txt".format(base_name), 'w+') as file:
        file.write('\n'.join(map(lambda t: "{}\t{}".format(t[0], t[1]),
                                 content_pages)))

    with open("out/{}_content.txt".format(base_name), "w+") as file:
        file.write('\n--------------------------------------------\n'.join(
            map(lambda t: '{}\n\n{}'.format(t[0], '\n----\n'.join(t[1])),
                content_dict.items())))
    return content_dict
