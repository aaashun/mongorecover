#! /bin/env python

import struct
import bson
import sys
#import pymongo

'''
valid bson physical format: int32 e_list 0x00
    1. the "int32"(little-endian) is the total number of bytes comprising the document
    2. the "e_list" is the elements of this document
    3. the "0x00" is the end flag of this document

removed bson physical format: 0xeeeeeeee e_list 0x00
    notice: the first 4 bytes was reset to 0xeeeeeeee

I found that the removed bson document starts with 0xeeeeeeee(4 bytes, size) and follow by ObjectId, and the ObjectId's first 4 bytes is [0x07, _, i, d]


so the way I recover the removed bson document is:
    find the removed document's start position, try to guess the right document size to replace '0xeeeeeeee'

reference: http://bsonspec.org/#/specification

PS: I recommend you parsing the dbfile in 'vim', and convert the content to hex format:
{{{
vim -b dbfile
:%!xxd
}}}
'''

#scan huge data, return next removed document's start position
def next_removed(data, start, size):
    i = start
    while i < size - 8:
        bson_size = struct.unpack("I", data[i:i+4])[0]
        if i % 4 == 0 and bson_size == 0xeeeeeeee and data[i+4] == chr(0x07) and data[i+5:i+8] == "_id":
            return i
        i += 4

    return -1


#connection = pymongo.Connection('localhost', 27017)
 
if __name__ == '__main__':

    DOCUMENT_MAX_SIZE = 1024*10

    if len(sys.argv) != 2:
        print 'usage: ' + sys.argv[0] + ' dbfile'
        exit()

    data = open(sys.argv[1],'rb').read()
    size = len(data)

    i = next_removed(data, 0, size)
    while i != -1 and i < size - 8:
        k = j = next_removed(data, i + 4, size)
        if k == -1 or (k - i) > DOCUMENT_MAX_SIZE:
            k = i + DOCUMENT_MAX_SIZE

        while k > i:
            if data[k] == chr(0x00):
                doc = None
                try:
                    doc = bson.decode_all(struct.pack('<i', k - i + 1) + data[i+4:k+1])[0]
                except Exception:
                    pass

                if doc != None:
                    print doc
                    # connection.foo_db.foo_collection.insert(doc)
                    break
            k -= 1

        i = j
