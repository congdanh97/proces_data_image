# -*- coding: utf-8 -*-
"""
Created on Wed Dec  9 13:46:20 2020

@author: admin
"""
import xml.etree.ElementTree as ET
import os
import ntpath
import glob
from pathlib import Path
import xml.etree.cElementTree as ET
from PIL import Image
import cv2



####get list name folder data xml
# list_name_foder = []
# wav_fpaths = list(Path("audio_data", "dataset").glob("**/*.wav"))
# str_old_name_folder = ""
# index_list_name_folder = 0


def indent(elem, level=0):
    i = "\n" + level * "\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def write_border_info_xml(xml_root, id_card_label, ls_box_border):
    ### border and type
    id_card = ET.SubElement(xml_root, 'border')
    id_card_type = ET.SubElement(id_card, 'type')
    id_card_type.text = id_card_label

    id_card_box = ET.SubElement(id_card, 'bbox')
    bbox = []
    for box_info in ls_box_border:
        if "Border" in box_info[0]:
            bbox = box_info[1]
    id_card_box_e = ET.SubElement(id_card_box, 'xmin')
    id_card_box_e.text = str(bbox[0])
    id_card_box_e = ET.SubElement(id_card_box, 'ymin')
    id_card_box_e.text = str(bbox[1])
    id_card_box_e = ET.SubElement(id_card_box, 'xmax')
    id_card_box_e.text = str(bbox[0] + bbox[2])
    id_card_box_e = ET.SubElement(id_card_box, 'ymax')
    id_card_box_e.text = str(bbox[1] + bbox[3])

    return xml_root


### info region: image, box, detail
### detail: label or idx, box, confidence
def write_region_info_xml(xml_root, label_region, info_region):
    xml_region = ET.SubElement(xml_root, 'region')
    ### summary info: label of region
    region_label = ET.SubElement(xml_region, 'label')
    region_label.text = str(label_region)
    bbox = info_region[1]
    ## region area
    region_box = ET.SubElement(xml_region, 'bbox')
    region_box_e = ET.SubElement(region_box, 'xmin')
    region_box_e.text = str(bbox[0])
    region_box_e = ET.SubElement(region_box, 'ymin')
    region_box_e.text = str(bbox[1])
    region_box_e = ET.SubElement(region_box, 'xmax')
    region_box_e.text = str(bbox[0] + bbox[2])
    region_box_e = ET.SubElement(region_box, 'ymax')
    region_box_e.text = str(bbox[1] + bbox[3])
    ### if have no detail, then return
    ls_detail = info_region[2]
    if len(ls_detail) < 1:
        return xml_root

    print(label_region)
    ## detail of digits or words inside region: label, box, confidence

    for info_detail in ls_detail:
        print(info_detail)
        region_detail = ET.SubElement(xml_region, 'detail')
        region_detail_label = ET.SubElement(region_detail, 'label')
        region_detail_label.text = str(info_detail[0])

        bbox = info_detail[1]
        region_detail_box = ET.SubElement(region_detail, 'bbox')
        region_detail_box_e = ET.SubElement(region_detail_box, 'xmin')
        region_detail_box_e.text = str(bbox[0])
        region_detail_box_e = ET.SubElement(region_detail_box, 'ymin')
        region_detail_box_e.text = str(bbox[1])
        region_detail_box_e = ET.SubElement(region_detail_box, 'xmax')
        region_detail_box_e.text = str(bbox[0] + bbox[2])
        region_detail_box_e = ET.SubElement(region_detail_box, 'ymax')
        region_detail_box_e.text = str(bbox[1] + bbox[3])

        region_detail_score = ET.SubElement(region_detail, 'score')
        region_detail_score.text = str(info_detail[2])

    return xml_root


# Write result xml:
def write_result_to_xml(str_img_path, id_card_label, ls_box_border, dict_region_crop):
    xml_root = ET.Element('annotation')
    str_folder = ntpath.dirname(str_img_path)
    str_name = ntpath.basename(str_img_path)

    xml_folder = ET.SubElement(xml_root, 'folder')
    xml_folder.text = str(str_folder)

    xml_name = ET.SubElement(xml_root, 'filename')
    xml_name.text = str(str_name)

    ### write info of border
    xml_root = write_border_info_xml(xml_root, id_card_label, ls_box_border)

    ### write each region
    for label in dict_region_crop:
        info_region = dict_region_crop[label]
        xml_root = write_region_info_xml(xml_root, label, info_region)

    mydata = ET.tostring(xml_root).decode()
    root = ET.fromstring(mydata)
    tree = ET.ElementTree(root)
    indent(root)
    tree.write("example.xml", encoding="utf-8", xml_declaration=True)


### read xml file

# def read_xml_yolo(xml_file, str_dir_img , str_dir_rs):
def read_xml_yolo(xml_file):
    str_dir_img = ""
    if not os.path.isfile(xml_file):
        print('not xml file')
        return []
    tree = ET.parse(xml_file)
    root = tree.getroot()
    str_name = ''

    for child in root:
        tag = child.tag
        if tag == 'folder':
            if len(str_dir_img) < 1:
                str_dir_img = child.text
        if tag == 'filename':
            str_name = child.text

    ### recognize all regions
    ls_name = []
    ls_box = []
    check = True
    min = -1
    max = -1
    # check =0
    top_left = [0, 0, 0, 0]

    for child in root:
        tag = child.tag
        if tag == 'object':
            ### warning change this method in next version
            ls_grand_child = child.getchildren()
            for grand_child in ls_grand_child:
                tag = grand_child.tag
                if 'name' == tag:
                    str_name_region = grand_child.text
                    ls_name.append(str_name_region)
                if 'bndbox' == tag:

                    x0 = (int)(grand_child.find('xmin').text)
                    y0 = (int)(grand_child.find('ymin').text)
                    x1 = (int)(grand_child.find('xmax').text)
                    y1 = (int)(grand_child.find('ymax').text)
                    bbox = [x0, y0, x1, y1]
                    ls_box.append(bbox)
                    min = x0 + y0
                    check = check + 1

    y_min_row = 999999
    x_max_row = -999999
    index1 = 0
    list_bb_1_row = []
    print("list box la:")
    print(ls_box)
    print("list box la:")

    root = ET.Element("annotation")
    ET.SubElement(root, "folder").text = xml_file.parent.name
    ET.SubElement(root, "filename").text = xml_file.name[:-4] + ".jpg"
    ET.SubElement(root, "path").text = str(xml_file)[:-4] + ".jpg"

    child_F1 = ET.SubElement(root, "source")

    ET.SubElement(child_F1, "database").text = "Unknown"

    #get width height image
    im = Image.open(str(xml_file)[:-4] + ".jpg")
    width, height = im.size

    chil_F1_1 = ET.SubElement(root, "size")

    ET.SubElement(chil_F1_1, "width").text = str(width)
    ET.SubElement(chil_F1_1, "height").text = str(height)
    ET.SubElement(chil_F1_1, "depth").text = "3"

    ET.SubElement(root, "segmented").text = "0"
    while (ls_box):
        y_min_all = 999999
        list_bb_1_row = []
        bb_min_row = [0, 0, 0, 0]
        bb_max_row = [0, 0, 0, 0]
        x0_min_row = 999999
        y1_max_row = -9999
        # 1 find bbox have y0 min (row top)
        for box in ls_box:
            if box[1] < y_min_all:
                y_min_all = box[1]
                box_y0_min_in_lsbox = box
        # print("bb min la :")
        # print(box_y0_min_in_lsbox)
        # 2 find box in 1 row append to 1 list\
        for bb in ls_box:
            if bb[1] < (box_y0_min_in_lsbox[1] + (box_y0_min_in_lsbox[3] - box_y0_min_in_lsbox[1]) / 2):
                list_bb_1_row.append(bb)
        for bb1 in list_bb_1_row:
            if bb1[0] < x0_min_row :
                x0_min_row = bb1[0]
                bb_min_row = bb1
            if bb1[2] > y1_max_row :
                y1_max_row = bb1[2]
                bb_max_row = bb1

            ls_box.remove(bb1)

        index1 = index1 + 1
        print("bb in row:" +  str(index1))
        print(list_bb_1_row)
        print(bb_min_row,bb_max_row)

        chil_F1_2 = ET.SubElement(root, "object")
        ET.SubElement(chil_F1_2, "name").text="cmt_row_" + str(index1-1)
        ET.SubElement(chil_F1_2, "pose").text="Unspecified"
        ET.SubElement(chil_F1_2, "truncated").text="0"
        ET.SubElement(chil_F1_2, "difficult").text="0"

        chil_F2_0 = ET.SubElement(chil_F1_2, "bndbox")
        ET.SubElement(chil_F2_0, "xmin").text = str(bb_min_row[0])
        ET.SubElement(chil_F2_0, "ymin").text = str(bb_min_row[1])
        ET.SubElement(chil_F2_0, "xmax").text = str(bb_max_row[2])
        ET.SubElement(chil_F2_0, "ymax").text = str(bb_max_row[3])

        tree = ET.ElementTree(root)
    tree.write(xml_file)

#load folder pt3
wav_xmls = list(Path("/home/congdanh/Desktop/", "pt4").glob("**/*.xml"))
index_xml = 0
for one_wav_xml in wav_xmls:
    min = 0
    print("Xu ly file thu:" + str(index_xml))
    read_xml_yolo(one_wav_xml)
    index_xml = index_xml + 1
    print(one_wav_xml.parent.name)

print("hello")