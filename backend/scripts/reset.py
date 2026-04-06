#!/usr/bin/env python3
import sqlite3                                                                                                                     
con = sqlite3.connect("backend/harvested/state.db")                                                                                
con.execute("DELETE FROM records WHERE source='teylers' AND collection='museum'")                                                  
con.commit()                                                                                                                       
print("Reset", con.total_changes, "records")   
