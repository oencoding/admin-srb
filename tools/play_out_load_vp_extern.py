#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Play Out load Vorproduktion von extern
Autor: Joerg Sorge
Org: SRB - Das Buergerradio
www.srb.fm

Distributed under the terms of GNU GPL version 2 or later
Copyright (C) Joerg Sorge joergsorge at goooglee
2011-09-30

Dieses Script stellt vorproduzierte Audio-Dateien 
fuer Sendungen (mp3-Dateien) 
im Play-Out-Server zur Verfuegung.
Dabei werden sie durch diverse Tools bearbeitet (z.B. mp3Gain)

Dateiname Script: play_out_load_vp_extern.py
Schluesselwort fuer Einstellungen: PO_VP_Config_1
Benoetigt: lib_common.py im gleichen Verzeichnis
Bezieht Daten aus: Firebird-Datenbank


Fehlerliste:
Error 000 Parameter-Typ oder Inhalt stimmt nich
Error 001 Fehler beim Kopieren der Vorproduktion in Play-Out
Error 002 beim mp3-Validator:
Error 003 bei mp3gain:
Error 004 Fehler beim Loeschen der mp3validator-bak-Datei
Error 005 Fehler beim Generieren des Dateinamens:

Parameterliste:
Param 1: Pfad vom Server zu Dropbox-Hauptordner
Param 2: Pfad vom Server zu Playout-Sendung
Param 3: Pfad/Programm mp3-validator
Param 4: Pfad/Programm mp3-gain

Ausfuehrung: jede Stunde zur Minute 45

In unserer Gesellschaft geht ein Gespenst um, 
das nur wenige deutlich sehen. 
Es ist nicht der alte Geist des Kommunismus oder des Faschismus. 
Es ist ein neues Gespenst: 
eine voellig mechanisierte Gesellschaft, 
die sich der maximalen Produktion 
und dem maximalen Konsum verschrieben hat 
und von Computern gesteuert wird.
Erich Fromm, Die Revolution der Hoffnung
"""

import time
import sys
import os
import string
import types
#import re
import datetime
import shutil
import subprocess
import ftplib
import socket
import lib_common as lib_cm


class app_config( object ):
    """Application-Config"""
    def __init__(self):
        """Einstellungen"""
        # app_config
        self.app_id = "005"
        self.app_desc = u"play_out_load_vp_extern"
        # schluessel fuer config in db
        self.app_config = u"PO_VP_extern_Config_3"
        self.app_config_develop = u"PO_VP_extern_Config_3_e"
        # anzahl parameter
        self.app_config_params_range = 5
        self.app_errorfile = "error_play_out_load_vp_extern.log"
        # errorlist
        self.app_errorslist = []
        self.app_errorslist.append(u"Error 000 Parameter-Typ oder Inhalt stimmt nicht ")
        self.app_errorslist.append(u"Error 001 Fehler beim Kopieren der Vorproduktion in Play-Out")
        self.app_errorslist.append(u"Error 002 beim mp3-Validator: ")
        self.app_errorslist.append(u"Error 003 bei mp3gain: ")
        self.app_errorslist.append(u"Error 004 Fehler beim Loeschen der mp3validator-bak-Datei")
        self.app_errorslist.append(u"Error 005 Fehler beim Generieren des Dateinamens: ")
        # params-type-list, typ entsprechend der params-liste in der config
        self.app_params_type_list = []
        self.app_params_type_list.append("p_string")
        self.app_params_type_list.append("p_string")
        self.app_params_type_list.append("p_string")
        self.app_params_type_list.append("p_string")
        self.app_params_type_list.append("p_string")
        
        # entwicklungsmodus (andere parameter, z.b. bei verzeichnissen)
        self.app_develop = "no"
        # meldungen auf konsole ausgeben
        self.app_debug_mod = "yes"
        self.app_windows = "no"
        self.app_encode_out_strings = "cp1252"
        #self.app_encode_out_strings = "utf-8"
        #self.time_target = datetime.datetime.now() + datetime.timedelta( days=-1 )
        #self.time_target = datetime.datetime.now() + datetime.timedelta(days=+1 )
        self.time_target = datetime.datetime.now()


def load_roboting_sgs(ac):
    """Sendungen suchen, die bearbeitet werden sollen"""
    lib_cm.message_write_to_console( ac, u"Sendungen suchen, die bearbeitet werden sollen" )
    sendungen_data = db.read_tbl_rows_with_cond(ac,  db,  "SG_HF_ROBOT", "SG_HF_ROB_TITEL, SG_HF_ROB_FILENAME", "SG_HF_ROB_VP ='T'" )
    
    if sendungen_data is None:
        log_message = u"Keine Sendungen fuer Uebernahme als VPs vorgesehen.. "
        #db.write_log_to_db( ac,  log_message, "t" )
        db.write_log_to_db_1(ac,  log_message, "t", "write_also_to_console" )
        return sendungen_data
    
    return sendungen_data

def load_sg(ac, sg_titel ):
    """Erstsendung suchen"""
    lib_cm.message_write_to_console( ac, u"Sendung suchen" )
    db_tbl_condition = "A.SG_HF_FIRST_SG ='T' AND SUBSTRING(A.SG_HF_TIME FROM 1 FOR 10) >= '" + str( ac.time_target.date() )+ "' " + "AND B.SG_HF_CONT_TITEL='"+ sg_titel +"' "
    sendung_data =  db.read_tbl_rows_sg_cont_ad_with_cond_2(ac, db, db_tbl_condition)
    
    if sendung_data is None:
        log_message = u"Keine Sendung mit diesem Titel gefunden: " + sg_titel
        #db.write_log_to_db( ac,  log_message, "t" )
        db.write_log_to_db_1(ac,  log_message, "t", "write_also_to_console" )
        return sendung_data
    
    return sendung_data

def audio_validate(ac, file_dest):
    """mp3-File validieren"""
    lib_cm.message_write_to_console( ac, u"mp3-File validieren" )
    #damit die uebergabe der befehle richtig klappt muessen alle cmds im richtigen zeichensatz encoded sein
    c_validator = db.ac_config_1[3].encode( ac.app_encode_out_strings )
    #c_validator = "/usr/bin/mp3val"
    c_source_file = file_dest.encode( ac.app_encode_out_strings )
    lib_cm.message_write_to_console( ac, c_source_file )
    # subprozess starten
    try:
        p = subprocess.Popen([c_validator, u"-f", c_source_file],  stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(  )
    except Exception, e:
        log_message = ac.app_errorslist[4] +u": %s" % str(e)
        db.write_log_to_db_1(ac, log_message, "x", "write_also_to_console" )
        return
    lib_cm.message_write_to_console( ac, u"returncode 0" )
    lib_cm.message_write_to_console( ac, p[0] )
    lib_cm.message_write_to_console( ac, u"returncode 1" )
    lib_cm.message_write_to_console( ac, p[1] )
    
    # erfolgsmeldung suchen, wenn nicht gefunden: -1
    validate_output = string.find( p[0],  "FIXED" )
    
    # wenn gefunden, position, sonst -1
    if validate_output != -1:
        log_message = u"mp3-Validator fixed: " + c_source_file
        db.write_log_to_db( ac, log_message, "k" )
        lib_cm.message_write_to_console( ac, "ok" )
        #bak-Datei löschen
        c_source_file = c_source_file + ".bak"
        delete_bak_ok = lib_cm.erase_file_1(ac, db, c_source_file,  u"mp3validator-bak-Datei geloescht " )    
        if delete_bak_ok is None:
            # Error 004 Fehler beim Loeschen der mp3validator-bak-Datei
            db.write_log_to_db_1(ac,  ac.app_errorslist[4], "x", "write_also_to_console")
    else:
        db.write_log_to_db_1(ac,  u"mp3-Validator fix offenbar nicht noetig: " + c_source_file, "p", "write_also_to_console" )
    
def audio_mp3gain(ac, path_file_dest):
    """mp3-File Gainanpassung"""
    lib_cm.message_write_to_console( ac, u"mp3-File Gainanpassung" )
    #damit die uebergabe der befehle richtig klappt muessen alle cmds im richtigen zeichensatz encoded sein
    c_mp3gain = db.ac_config_1[4].encode( ac.app_encode_out_strings )
    c_source_file = path_file_dest.encode( ac.app_encode_out_strings )
    lib_cm.message_write_to_console( ac, c_source_file )
    # subprozess starten
    try:
        p = subprocess.Popen([c_mp3gain, u"-r", c_source_file],  stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(  )
    except Exception, e:
        log_message = ac.app_errorslist[3] + u": %s" % str(e)
        db.write_log_to_db_1(ac, log_message, "x", "write_also_to_console" )
        return

    lib_cm.message_write_to_console( ac, u"returncode 0" )
    lib_cm.message_write_to_console( ac, p[0] )
    lib_cm.message_write_to_console( ac, u"returncode 1" )
    lib_cm.message_write_to_console( ac, p[1] )
    
    # erfolgsmeldung suchen, wenn nicht gefunden: -1
    mp3gain_output = string.find( p[1],  "99%" )
    mp3gain_output_1 = string.find( p[1],  "written" )
    lib_cm.message_write_to_console( ac, mp3gain_output )
    lib_cm.message_write_to_console( ac, mp3gain_output_1 )
    # wenn gefunden, position, sonst -1
    if mp3gain_output != -1 and mp3gain_output_1 != -1:
        log_message = u"mp3gain angepasst: " + c_source_file
        db.write_log_to_db( ac, log_message, "k" )
        lib_cm.message_write_to_console( ac, "ok" )
    else:
        db.write_log_to_db_1(ac,  u"mp3gain offenbar nicht noetig: " + c_source_file, "p", "write_also_to_console" )

def check_and_work_on_files(roboting_sgs):
    """ 
    - Zugehoerige Audios suchen 
    - wenn vorhanden, bearbeiten 
    """
    lib_cm.message_write_to_console(ac, u"check_and_work_on_files" )
    
    for item in roboting_sgs:
        lib_cm.message_write_to_console( ac, item[0].encode('ascii', 'ignore') )
        titel = item[0]
        # Pfad-Datei und Titel nach Datums-Muster teilen
        l_path_title = item[1].split("yyyy_mm_tt")    
        # Sendung suchen
        sendung = load_sg(ac, titel)
        
        if sendung is None:
            lib_cm.message_write_to_console(ac, u"Keine Sendungen gefunden" )
            continue
        
        #db.write_log_to_db_1(ac, u"Sendung fuer VP-Uebernahme gefunden: "+sendung[0][11], "t", "write_also_to_console" )
        db.write_log_to_db_1(ac, u"Sendung fuer VP-Uebernahme gefunden: "+sendung[0][11].encode('ascii', 'ignore'), "t", "write_also_to_console" )
        
        try:
            #lib_cm.message_write_to_console(ac, l_titel_file[1] )
            path_source = lib_cm.check_slashes(ac, db.ac_config_1[1]) 
            #path_file_source = path_source + l_path_title[0] + sendung[0][2].strftime('%Y_%m_%d') + l_path_title[1]
            path_file_source = path_source + l_path_title[0] + sendung[0][2].strftime('%Y_%m_%d') + l_path_title[1].rstrip()
            path_dest = lib_cm.check_slashes(ac, db.ac_config_1[2])
            # replace_sonderzeichen_with_latein
            #path_file_dest = path_dest + str(sendung[0][8]) + "_" + sendung[0][16] + "_" + sendung[0][13] + ".mp3"
            path_file_dest = path_dest + str(sendung[0][8]) + "_" + sendung[0][16] + "_" + lib_cm.replace_sonderzeichen_with_latein( sendung[0][13]) + ".mp3"
        except Exception, e:
            log_message = ac.app_errorslist[5] + str(e)
            db.write_log_to_db_1(ac, log_message, "x", "write_also_to_console" )
            continue
        
        lib_cm.message_write_to_console(ac, path_file_source )
        lib_cm.message_write_to_console(ac, path_file_dest )

        if not os.path.isfile( path_file_source ):
            lib_cm.message_write_to_console( ac, u"nicht vorhanden: "+ path_file_dest )
            db.write_log_to_db_1(ac, u"Audio Vorproduktion noch nicht vorhanden: "+ path_file_source, "f", "write_also_to_console" )
            continue

        if os.path.isfile( path_file_dest ):
            lib_cm.message_write_to_console( ac, u"vorhanden: "+ path_file_dest )
            db.write_log_to_db_1(ac, u"Audiodatei fuer Sendung bereits vorhanden: "+ path_file_dest, "k", "write_also_to_console" )
            continue
            
        # In Play-Out kopieren
        try:
            shutil.copy( path_file_source, path_file_dest )
            db.write_log_to_db_1(ac, u"Audio Vorproduktion: "+ path_file_source, "v", "write_also_to_console" )
            db.write_log_to_db_1(ac, u"Audio kopiert nach: "+ path_file_dest, "c", "write_also_to_console" )
        except Exception, e:
            db.write_log_to_db_1(ac,  ac.app_errorslist[1], "x", "write_also_to_console" )
            log_message = u"copy_files_to_dir_retry Error: %s" % str(e)
            lib_cm.message_write_to_console( ac, log_message )
            db.write_log_to_db(ac, log_message, "x" )
            continue        
        #path_file_dest = "/home/workshop-2/projects-develop/SRB_Source_Tools/" + path_file_dest
        audio_validate(ac, path_file_dest)
        audio_mp3gain(ac, path_file_dest)
        # filename rechts von slash extrahieren
        if ac.app_windows == "no":
            filename = path_file_dest[string.rfind(path_file_dest,  "/")+1:]
        else:
            filename = path_file_dest[string.rfind(path_file_dest,  "\\")+1:]
            
        db.write_log_to_db_1(ac, "VP bearbeitet: " + filename, "i", "write_also_to_console" )
        db.write_log_to_db_1(ac, "VP bearbeitet: " + filename, "n", "write_also_to_console" )


def lets_rock():
    """Hauptfunktion """
    print "lets_rock " 
    # Sendungen suchen, die bearbeitet werden sollen
    roboting_sgs = load_roboting_sgs(ac)
    if roboting_sgs is None:
        return
        
    # pruefen was noch nicht im play_out ist und kopieren und bearbeiten 
    check_and_work_on_files(roboting_sgs)
    return


if __name__ == "__main__":
    db = lib_cm.dbase()
    ac = app_config()
    print  "lets_work: " + ac.app_desc 
    # losgehts
    db.write_log_to_db(ac,  ac.app_desc + u" gestartet", "a")
    # Config_Params 1
    db.ac_config_1 = db.params_load_1(ac,  db)
    if db.ac_config_1 is not None:
        lets_rock()

    # fertsch
    db.write_log_to_db(ac,  ac.app_desc + u" gestoppt", "s")
    print "lets_lay_down"
    sys.exit()