#!/bin/python
"""
Convert Gold Standard XML data to tidy format
"""

__version__ = "0.4"
__author__ = "Keith Yip"
# $Source$


import sys
from os import path
import argparse
import xml.etree.ElementTree as ElementTree
import errno
import csv


class NoClobberError(Exception):
    """
    An exception class that is raised when the tool is about to overwrite something when the noclobber option
    is specified
    """
    def __init__(self, clobberfile):
        self.clobberfile = clobberfile


class CategoryNotFoundError(Exception):
    """
    An exception class that is raised if a requested category is not found in the category.xml
    """
    def __init__(self, categoryname):
        self.categoryname = categoryname


class ColumnNotFoundError(Exception):
    def __init__(self, colname):
        self.colname = colname


class TidyDialect(csv.Dialect):
    delimiter = ','
    doublequote = True
    quotechar = "\""
    escapechar = "\\"
    lineterminator = "\r\n"
    quoting = csv.QUOTE_MINIMAL


class VersionAction(argparse.Action):
    def __call__(self, *args, **kwargs):
        print path.basename(__file__) + " " + __version__
        if len(sys.argv) == 2:
            sys.exit()


def parse_args():
    """
    Parse the argument for this tool
    :return: a Namespace class containing all the specified arguments
    """
    parser = argparse.ArgumentParser(description='Convert golden standard XML data to tidy format.')
    parser.add_argument("inputFile", metavar='INPUT_FILE', type=str, nargs='?', default=None, help='name of input file')
    parser.add_argument("-o", "--output", metavar='OUTPUT_FILE', type=str, help='name of output file')
    parser.add_argument('--category', metavar='CATPATH', type=str, help='filepath to the category xml')
    parser.add_argument('--catname1', type=str, help='name for category 1')
    parser.add_argument('--catname2', type=str, help='name for category 2')
    parser.add_argument('--catname3', type=str, help='name for category 3')
    parser.add_argument("--noheader", action="store_true", help='omit header file')
    parser.add_argument("--noclobber", action="store_true", help="prevent unintentional clobbering")
    parser.add_argument("--quiet", action="store_true", help="suppress standard output")
    parser.add_argument("--version", nargs=0, action=VersionAction, help="display version number")
    parser.add_argument("--upc", type=str, help="EAN/UPC of the output drink")
    parser.add_argument("--temp", type=str, help="liquid temperature of the output drink")
    col_group = parser.add_mutually_exclusive_group()
    col_group.add_argument("--column", type=str, help="define the columns to be outputted: " +
                                                      field_names(None, []).__repr__())
    col_group.add_argument("--exclude", type=str, help="exclude the columns from being outputted")
    return parser.parse_args()


def get_categories(opts, tree):
    """
    Get category info from the tree
    :param opts: arguments for this tool
    :param tree: the data tree
    :return: a dict containing category info
    """
    if opts.category is None:
        cate = None
    else:
        cate = ElementTree.parse(opts.category).getroot()
    cat1 = get_category(opts.catname1, tree.find('Category1'), 'First', cate)
    cat2 = get_category(opts.catname2, tree.find('Category2'), 'Second', cate)
    cat3 = get_category(opts.catname3, tree.find('Category3'), 'Third', cate)
    return {'name1': cat1[0], 'guid1': cat1[1], 'name2': cat2[0],
            'guid2': cat2[1], 'name3': cat3[0], 'guid3': cat3[1]}


def get_category(opts_name, categ_name, tag, categ):
    """
    Get one category from the data tree
    :param opts_name: the category name as specified from the command argument
    :param categ_name: the category name as specified from the drink.xml
    :param tag: the tag of the category, can be 'First', 'Second', or 'Third'
    :param categ: the category data tree
    :return: a pair that describes the category name and the category GUID
    """
    if opts_name is not None:
        return opts_name, find_category_guid(opts_name, tag, categ)
    if categ_name is not None:
        return categ_name, find_category_guid(categ_name, tag, categ)
    return '', ''


def find_category_guid(name, tag, categ):
    """
    Find category GUID from the category.xml data tree
    :param name: the category name
    :param tag: the tag of the category, can be 'First', 'Second' or 'Third'
    :param categ: the categoy data tree
    :return: category GUID
    """
    if categ is None:
        return ''

    if categ.find(tag) is None:
        return ''

    result = [x[0].text for x in categ.find(tag) if x.attrib['Name'] == name]
    if len(result) == 0:
        return ''

    return result[0]


def get_output_file(opts):
    """
    Determine the output file based on the command arguments
    :param opts: command arguments
    :return: output file
    """
    if opts.output is None or opts.output == "-":
        # Output is stdout.
        return sys.stdout
    elif path.isdir(opts.output):
        # Output is a directory.
        base_file, ext = path.splitext(path.basename(opts.inputFile))
        output_file = path.join(opts.output, base_file + ".csv")
    else:
        # Output is a regular file.
        base_file, ext = path.splitext(opts.output)
        output_file = opts.output + ".csv" if ext == '' else opts.output

    if path.exists(output_file) and opts.noclobber:
        raise NoClobberError(output_file)
    return open(output_file, 'w')


def get_input_data(tree, opts):
    """
    Get the drink.xml data into a hash and return the hash
    :param tree: the data tree
    :param opts: command argument
    :return: dict that contains the data to be emitted to the output file
    """
    result = {'name': tree.find('Name').text,
              'drink_id': tree.find('DrinkIdStr').text,
              'upc': get_upc(tree, opts)}
    ref = tree.find('Reflectance')
    if ref is not None:
        result['ref'] = get_exp_data(ref, opts)
    tra = tree.find('Transmission')
    if tra is not None:
        result['tra'] = get_exp_data(tra, opts)
    return result


def get_temp(tree, opts):
    """
    Get the temperature from either the data tree or the command argument
    :param tree: data tree
    :param opts: command argument
    :return: liquid temperature
    """
    if opts.temp is not None:
        if not opts.quiet:
            print "gsxmltidy: warning: overriding liquid temperature from gsfile"
        return opts.temp
    temp = tree.find('LiquidTemperature')
    if temp is None:
        if not opts.quiet:
            print "gsxmltidy: warning: cannot find liquid temperature"
        return ''
    return temp.text


def get_upc(tree, opts):
    """
    Get the drink Ean/Upc from either the data tree or the command argument
    :param tree: data tree
    :param opts: command arguemnt
    :return: Ean/UPC
    """
    if opts.upc is not None:
        if not opts.quiet:
            print "gsxmltidy: warning: overriding upc/ean from gsfile"
        return opts.upc
    upc = next(item[1][0].text for item in tree.find('Details')
               if item[0][0].text == 'Ean')
    if upc is None:
        if not opts.quiet:
            print "gsxmltidy: warning: cannot find upc"
        return ''
    return upc


def get_dark_or_white(tree, dark_or_white):
    """
    Get dark or white data from the data tree
    :param tree: the data tree
    :param dark_or_white: 'd' if dark, 'w' if white
    :return: dark/white data
    """
    if dark_or_white == 'd':
        csv_entry, csv_list = 'DarkCsv', 'DarkListCsv'
    elif dark_or_white == 'w':
        csv_entry, csv_list = 'WhiteCsv', 'WhiteListCsv'
    else:
        raise ValueError('get_dark_or_white must specify "d" or "w" as dark_or_white parameter')

    length = int(tree.find('NumberOfScans').text)
    pixels = int(tree.find('Pixels').text)
    single_entry = tree.find(csv_entry)

    if single_entry is not None and len(single_entry) != 0:
        return [single_entry.text.split(',')] * length

    multiple_entry = tree.find(csv_list)
    if multiple_entry is not None and len(multiple_entry) != 0:
        intensities_list = [intensities.text.split(',')
                            for intensities in multiple_entry]

        average_copy = [average_for_struct(zipped_wavelength)
                        for zipped_wavelength in zip(*intensities_list)]

        return [average_copy] * length
    
    return [['0'] * pixels] * length


def average_for_struct(struct):
    return str(sum(map(float, struct)) / float(len(struct)))


def get_exp_data(tree, opts):
    """
    Get transmission/reflectance data
    :param tree: the data tree
    :param opts: command arguments
    :return: the dict containing data about the experiment
    """
    return {'serial_number': tree.find('SerialNumber').text,
            'integration_time': tree.find('IntegrationTime').text,
            'wavelengths': tree.find('WavelengthsCsv').text.split(','),
            'dark': get_dark_or_white(tree, 'd'),
            'white': get_dark_or_white(tree, 'w'),
            'read': [x.text.split(',') for x in tree.find('IntensitiesListCsv')],
            'read_date': tree.find('ExperimentRecordedStr').text,
            'dark_date': tree.find('DarkRecordedStr').text,
            'white_date': tree.find('WhiteRecordedStr').text,
            'temp': get_temp(tree, opts),
            'xsmooth': try_get_text(tree, 'XSmooth'),
            'tempcomp': try_get_text(tree, 'IsTemperatureCompensated'),
            'scans_to_avg': try_get_text(tree, 'ScansToAverage'),
            'xtrate': try_get_text(tree, 'XTimingResolution')}


def try_get_text(tree, target):
    """
    Attempt to get the XML element 'target' from the tree.  If
    failed, return an empty string, otherwise, return the text
    for that element
    :param tree: the XML tree to search from
    :param target: the target element to search
    :return: empty string if target cannot be found, otherwise,
    the text under the target's element
    """
    target_leaf = tree.find(target)

    if target_leaf is None:
        return ''
    else:
        return target_leaf.text


def emit_output(indata, categ, writer):
    """
    Emit data to output
    :param indata: input data
    :param categ: category data
    :param output: output file
    :return: none
    """
    if 'ref' in indata:
        emit_body(indata, categ, indata['ref'], writer, 'r')
    if 'tra' in indata:
        emit_body(indata, categ, indata['tra'], writer, 't')


def emit_body(indata, categ, exp, writer, mode):
    """
    Emit the body of data to output
    :param indata: input data
    :param categ: category data
    :param exp: experiment data
    :param output: output file
    :param mode: whether it is transmission ('t') or reflectance ('r')
    :return: none
    """
    for observation, read in enumerate(exp['read']):
        for wavelength, wavelengthVal in enumerate(exp['wavelengths']):
            row = {
                'name': indata['name'] or '',  # 00
                'drink.id': indata['drink_id'] or '',  # 01
                'category.name.1': categ['name1'] or '',  # 02
                'category.guid.1': categ['guid1'] or '',  # 03
                'category.name.2': categ['name2'] or '',  # 04
                'category.guid.2': categ['guid2'] or '',  # 05
                'category.name.3': categ['name3'] or '',  # 06
                'category.guid.3': categ['guid3'] or '',  # 07
                'observation': observation,  # 08
                'wavelength': wavelengthVal,  # 09
                'reading': read[wavelength] or '',  # 10
                'white': exp['white'][observation][wavelength] or '',  # 11
                'dark': exp['dark'][observation][wavelength] or '',  # 12
                'reading.date': exp['read_date'] or '',  # 13
                'white.date': exp['white_date'] or '',  # 14
                'dark.date': exp['dark_date'] or '',  # 15
                'upc': indata['upc'] or '',  # 16
                'temp': exp['temp'] or '',  # 17
                'integration.time': exp['integration_time'] or '',  # 18
                'serial.number': exp['serial_number'] or '',  # 19
                'protocol': mode or '',  # 20
                'scans.to.avg': exp['scans_to_avg'] or '',  # 21
                'xsmooth': exp['xsmooth'] or '',  # 22
                'temp.comp': exp['tempcomp'] or '',  # 23
                'xtrate': exp['xtrate'] or '',  # 24
            }
            writer.writerow(dict((k, v.encode('utf-8') if type(v) is unicode else v) for k, v in row.iteritems()))


def field_names(col_include, col_exclude):
    """
    Emit the header
    :return: the header
    """
    default = ['name', 'drink.id', "category.guid.1", "category.name.1", "category.guid.2",
               "category.name.2", "category.guid.3", "category.name.3", 'observation', 'wavelength', 'reading', 'white',
               'dark', 'reading.date', 'white.date', 'dark.date', 'upc', 'temp', 'integration.time', 'serial.number',
               'protocol', 'scans.to.avg', 'xsmooth', 'temp.comp', 'xtrate']

    if col_include is not None:
        for col in col_include:
            if col not in default:
                raise ColumnNotFoundError(col)

        return col_include

    if col_exclude is not None:
        for col in col_exclude:
            if col not in default:
                raise ColumnNotFoundError(col)
        return [col for col in default if col not in col_exclude]

    return default


args = parse_args()
try:
    with get_output_file(args) as out:
        col_include = args.column.split(',') if args.column is not None else None
        col_exclude = args.exclude.split(',') if args.exclude is not None else None

        writer = csv.DictWriter(out, field_names(col_include, col_exclude),
                                extrasaction='ignore', dialect=TidyDialect)

        root = ElementTree.parse(args.inputFile or sys.stdin).getroot()
        categories = get_categories(args, root)
        input_data = get_input_data(root, args)

        if not args.noheader:
            writer.writeheader()

        emit_output(input_data, categories, writer)

        if not args.quiet:
            print "gsxmltidy: converted " + (args.inputFile or "stdin") + " to " + out.name

except ElementTree.ParseError as e:
    print >> sys.stderr, "gsxmltidy: problem parsing xml files: " + e.message.message
except IOError as e:
    if e.errno != errno.EPIPE:
        print >> sys.stderr, "gsxmltidy: problem opening specified files in command args: " + e.strerror
except NoClobberError as ex:
    print >> sys.stderr, "gsxmltidy: cannot overwrite output file under noclobber: " + ex.clobberfile
except CategoryNotFoundError as ex:
    print >> sys.stderr, "gsxmltidy: cannot find category from command args or in input file: " + ex.categoryname
except ColumnNotFoundError as ex:
    print >> sys.stderr, "gsxmltidy: cannot find column: " + ex.colname
    # except AttributeError:
    # print >> sys.stderr, "gsxmltidy: input file has valid xml, but data is not valid"

