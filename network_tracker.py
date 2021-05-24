#!/usr/bin/env python3

import dpkt
import socket
import pygeoip
import argparse
from requests import get

#import dataset
gi = pygeoip.GeoIP("GeoLiteCity.dat")

# utilise ipify api to query external IP
def getIP():
    ip = get('https://api.ipify.org').text
    return(ip)

# get long/lat for ip, add to KML format
def retKML(dstIP, srcIP):
    dst = gi.record_by_name(dstIP)
    src = gi.record_by_name(srcIP)
    try:
        dstLong = dst['longitude']
        dstLat = dst['latitude']
        srcLong = src['longitude']
        srcLat = src['latitude']
        kml = (
            '<Placemark>\n'
            '<name>%s</name>\n'
            '<extrude>1</extrude>\n'
            '<tessellate>1</tessellate>\n'
            '<styleUrl>#transBluePoly</styleUrl>\n'
            '<LineString>\n'
            '<coordinates>%6f,%6f\n%6f,%6f</coordinates>\n'
            '</LineString>\n'
            '</Placemark>\n'
        )%(dstIP, dstLong, dstLat, srcLong, srcLat)
        return kml
    except:
        return ''

# return pts based on IP
def plotIPs(pcap):
    pts = ""
    parsedTotal = 0
    parsedErrors = 0
    ptsArr = []
    srcIP = getIP()
    
    for (ts, buf) in pcap:
        parsedTotal += 1
        try:
            eth = dpkt.ethernet.Ethernet(buf)
            ip = eth.data
            src = socket.inet_ntoa(ip.src)
            dst = socket.inet_ntoa(ip.dst)
            if dst in ptsArr:
                pass
            else:
                ptsArr.append(dst)
                KML = retKML(dst, srcIP)
                pts = pts + KML
        except:
            parsedErrors += 1
    print(ptsArr)
    print(f"Total Reads: {parsedTotal}\nRead errors: {parsedErrors}\nRead error percentage: {parsedErrors/parsedTotal:.4f}")
    return pts

# main function for execution
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('infile', help = "PCAP file for plotting")
    parser.add_argument('outfile', nargs="?", help = "Specified file to write to. Defaults to \'newKML.kml\'")
    args = parser.parse_args()

    try:
        file = open(args.infile, 'rb')
    except:
        print(f"ERROR: Unable to open {args.infile}")
        exit(1)

    try:
        pcap = dpkt.pcap.Reader(file)
    except:
        print(f"ERROR: Unable process {args.infile} as PCAP")
        exit(1)

    kmlheader = '<?xml version="1.0" encoding="UTF-8"?> \n<kml xmlns="http://www.opengis.net/kml/2.2">\n<Document>\n'\
                '<Style id="transBluePoly">' \
                '<LineStyle>' \
                '<width>1.5</width>' \
                '<color>501400E6</color>' \
                '</LineStyle>' \
                '</Style>'
    kmlfooter = '</Document>\n</kml>\n'
    kmldoc=kmlheader+plotIPs(pcap)+kmlfooter

    with open((args.outfile if args.outfile else "newKML.kml"), "w") as f:
        f.write(kmldoc)
    file.close()



if __name__ == "__main__":
    main()
