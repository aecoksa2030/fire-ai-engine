/**
 * Fixed engineering BOQ prompts for HCIS-classified substation security
 * drawings, supplied by the client as four Word documents per substation
 * class ("Class 1 – 380KV Substations" and "Class 3 – Smaller
 * Substations"). These are selectable directly from the drawing chat
 * (see components/drawing-chat.tsx) whenever the current report type is
 * "security" — picking a class + topic sends the exact prompt text below
 * as the chat question, verbatim, instead of the user having to retype or
 * paste it from the original document each time.
 *
 * Each of the 4 topics per class is designed to be asked independently
 * against the same drawing/session (Prompts 1–3 results feed into Prompt
 * 4's BOQ per the source documents), so these are exposed as one topic
 * picker rather than one single mega-prompt.
 */

export type SubstationClass = "class1" | "class3";
export type SecurityPromptKey =
  | "video_access"
  | "personnel_fence"
  | "physical_equipment"
  | "electrical_ups";

export const SUBSTATION_CLASS_OPTIONS: { value: SubstationClass; label: string }[] = [
  { value: "class1", label: "Class 1 – 380KV Substations" },
  { value: "class3", label: "Class 3 – Smaller Substations" },
];

export const SECURITY_PROMPT_OPTIONS: { value: SecurityPromptKey; label: string }[] = [
  { value: "video_access", label: "Prompt 1 – Video Surveillance, Access Control, Intercom, IP Telephone" },
  { value: "personnel_fence", label: "Prompt 2 – Personnel Search Equipment, Fence & Network Switches" },
  { value: "physical_equipment", label: "Prompt 3 – Physical Security Equipment (Gates, Barriers, Bollards)" },
  { value: "electrical_ups", label: "Prompt 4 – Lighting, Electrical, UPS & Generator" },
];

export const SECURITY_PROMPTS: Record<SubstationClass, Record<SecurityPromptKey, string>> = {
  class1: {
    video_access: `Class-1 380 KV Substations HCIS Requirements
## Role
Act as a **Senior Physical Security Estimation Engineer
Your specialization includes:
- CCTV / Video Surveillance System
- Video Management System (VMS)
- Access Control System (ACS)
- Intercom
- IP Telephone
- Automatic Number Plate Recognition (ANPR/LPR)
- Security Servers, Workstations and Storage
- Intrusion Detection System (IDS)
- Perimeter Intrusion Detection System (PIDS)
Perimeter:
External PTZ camera – Every 250 meters with 7-meter poles
Short range fixed camera- for each transformer (Critical assets) with 3-meter pole
Fiber optic perimeter sensing system (FOPSS)- Maximum zone limit 150 meters
Microwave Intrusion Detection System (MIDS)- Maximum zone limit 150 meters, Corners should have transceivers (1.2-meter pole)
Intrusion detection and Assessment system (IDAS):
External fixed camera – Maximum 75 meters distance with VA (5 Meter pole)
Main Entrance Gate:
Short Range fixed camera – One for each Lane for monitoring and one for card reader monitoring (3-meter pole)
Gate PTZ camera- Both entry and exit side of the gatehouse. (5-meter pole)
Card Readers- Both Entry and Exit lanes (1.2-meter pole)
Video Intercom- Both Entry and Exit lanes (1.2-meter pole)
Pedestrian Gate: (or Turnstile)
Outdoor Dome camera- Outdoor dome camera for each in and out card readers
Card readers- for In and Out
Video Intercom – For in and out
Gatehouse:
Outdoor Dome camera- Outdoor dome camera for Entrance card reader
Card readers- for entrance, with Push button, Break glass unit, Magnetic locks, Door contacts
ISS workstation
ALPR workstation
UVIS workstation
Two IP Telephone
ACS controller with power supply to be provided in a Gate house
Preliminary Inspection checkpoint:
One IP Telephone
Emergency Gate:
One fixed camera to monitor the gate.
Telecom shelter: (For SEC)
Short range fixed camera – for monitoring the gate
Security Building:
In and outside card readers with dome cameras, Break glass unit, Magnetic locks, Door contacts to be provided for All Doors.
ACS controller with power supply to be provided in a security room.
ISS server (Main and redundant, Server sizing based on the number of cameras), Network video recorder (Main and redundant, recorder Server sizing based on the number of cameras), Access control Server (Main and redundant)
380KV GIS Building:
Single entry card readers on the entry side with dome cameras, Break glass unit, Magnetic locks, Door contacts to be provided for All Doors.
Emergency exit doors on the staircase side, to be provided with dome camera, door contacts and siren.
ACS controller with power supply to be provided.
132KV GIS Building:
Single entry card readers on the entry side with dome cameras, Break glass unit, Magnetic locks, Door contacts to be provided for All Doors.
Emergency exit doors on the staircase side, to be provided with dome camera, door contacts and siren.
ACS controller with power supply to be provided.
13.8KV Switchgear building:
Single entry card readers on the entry side with dome cameras, Break glass unit, Magnetic locks, Door contacts to be provided for All Doors.
Emergency exit doors on the staircase side, to be provided with dome camera, door contacts and siren.
ACS controller with power supply to be provided.
Control building:
In and out card readers with dome cameras, Break glass unit, Magnetic locks, Door contacts to be provided for All Doors entrance of control room.
Emergency exit doors on the staircase side, to be provided with dome camera, door contacts and siren.
ACS controller with power supply to be provided.
One IP Telephone
Cable tunnel:
Single entry card readers on the entry side with dome cameras, Break glass unit, Magnetic locks, Door contacts to be provided for All Doors.
Storage calculation:
Perimeter External PTZ camera- for continuous recording 8 Fps, 720P, 2 months, H.265
For Motion recording 30 fps, 1080P, 5%
Perimeter External fixed camera- for continuous recording 8 Fps, 720P, 2 months, H.265
For Motion recording 30 fps, 1080P, 5%
Short range fixed camera- for continuous recording 8 Fps, 720P, 3 months, H.265
For Motion recording 30 fps, 1080P, 5%
Buildings dome camera (indoor/outdoor)- for continuous recording 8 Fps, 720P, 3 months,
For Motion recording 30 fps, 1080P, 5%, H.265
Gate External PTZ camera- for continuous recording 8 Fps, 720P, 1 month, H.265
For Motion recording 30 fps, 1080P, 5%
## Action
Create the full Bill of Quantities using the details provided above.`,

    personnel_fence: `Class-1 380 KV substations HCIS Requirements
## Role
Act as a **Senior Physical Security Estimation Engineer
Your specialization includes:
- Category - 1 Anti-personnel fence
- Category-1 Anti Vehicle Barrier
- Hand Held Explosives Detector
- Hand Held Metal Detector
- Fiber Optic Infrastructure
- Network cable (CAT 6) Infrastructure
- Signal Cable Infrastructure
- Security Networks
Perimeter:
Category 1 Fencing with Anti vehicle barrier
FEC cabinet- Every 150 meters on the perimeter with single-mode fibre connectivity from the security building, it has to be provided with Industrial ethernet switches (switches port numbers based on the Number of cameras, FOPSS controller, MIDS), Fiber patch panel, UTP patch panel, splicing box.
Every 250 meters on the perimeter, one PTZ camera for cable calculation, CAT6 (Outdoor) cable connects to the nearest Industrial Ethernet switches
Every 75 meters on perimeter one VA camera for cable calculation, CAT6 (Outdoor) cable connects to the nearest Industrial Ethernet switches
Every 150 meters perimeter one (FOPSS) controller for fiber sensor cable calculation to connect near to the switch
Every 75 meters on perimeter one (MIDS) controller for cable calculation, CAT6 (Outdoor) cable connects to the nearest Industrial Ethernet switches
Main Entrance Gate:
Handheld Explosives Detector- 1 no
Handheld Metal Detector -1 no
Short Range fixed camera – One for each Lane for cable calculation, CAT6 (Outdoor) cable connects to the nearest the Ethernet switches
Gate PTZ camera- Both entry and exit side of the gatehouse for each Lane for cable calculation, CAT6 (Outdoor) cable connects to the nearest Ethernet switches
Card Readers- Both Entry and Exit lanes for cable calculation Signal Cable connects to the nearest Access control Panel
Video Intercom- Both Entry and Exit lanes for cable calculation, CAT6 (Outdoor) cable connects to the nearest the Ethernet switches
ALPR- For entry side for cable calculation, CAT6 (Outdoor) cable connects to the nearest Ethernet switches
UVIS- for entry side for cable calculation, CAT6 (Outdoor) cable connects to the nearest Ethernet switches
Pedestrian Gate: (or Turnstile)
Outdoor Dome camera- In and Out Outdoor for cable calculation, CAT6 (Outdoor) cable connects to the nearest Ethernet switches
Card readers- for In and Out for Signal Cable calculation for cable calculation Signal Cable connects to the nearest Access control Panel
Video Intercom – For in and out for cable calculation, CAT6 (Outdoor) cable connects to the nearest the Ethernet switches
Gatehouse:
Outdoor Dome camera- Outdoor dome camera for Entrance card reader, for cable calculation, CAT6 (Outdoor) cable connects to the nearest Ethernet switches
Card readers- for entrance, with Push button, Break glass unit, Magnetic locks, Door contacts, for cable calculation Signal Cable connects to the nearest Access control Panel
Road blocker control switch, for cable calculation Signal Cable calculation connected to the road blocker
Raise arm barrier control switch, for cable calculation Signal Cable calculation connected to the Raise arm barrier
Turnstile control switch, for cable calculation Signal Cable calculation connected to the Turnstile
ISS workstation, for cable calculation, CAT6 (Indoor) cable connects to the nearest Ethernet switches
ALPR workstation, for cable calculation, CAT6 (Indoor) cable connects to the nearest Ethernet switches
UVIS workstation, for cable calculation, CAT6 (Indoor) cable connects to the nearest Ethernet switches
Emergency Alarm Button/Panic alarm button for Signal Cable calculation
Outdoor siren- 2 Nos, for entry side and exit side for Signal Cable calculation
1 Dedicated 15U server rack to be provided to keep the Access switches (switches port numbers based on the Number of cameras and Access control panels), Fiber patch panel, UTP patch panel, for fibre cable calculation, single-mode fibre connectivity from the security building to the gatehouse
Emergency Gate:
One fixed camera to monitor the gate, for cable calculation, CAT6 (outdoor) cable connects to the nearest industrial Ethernet switches
Magnetic boundary sensor for the gates, for cable calculation, Signal Cable calculation connected to the FEC
Security Building:
2 Dedicated 42 U server rack to be provided in security room, to keep the Core (switches the port numbers based on the access switches), Access switches (switches port numbers based on the Number of cameras and Access control panels), KVM switch, Fiber patch panel, UTP patch panel, cable manager.
In and outside card readers with dome cameras, Break glass unit, Magnetic locks, Door contacts to be provided for All Doors. for cable calculation Signal Cable connects to the nearest Access control Panel and for Network cable calculation, dome camera's CAT6 (Indoor) cable connects to the nearest industrial Ethernet switches
380KV GIS Building:
Single entry card readers on the entry side with dome cameras, Break glass unit, Magnetic locks, Door contacts to be provided for All Doors. for cable calculation Signal Cable connects to the nearest Access control Panel and for Network cable calculation, dome camera's CAT6 (Indoor) cable connects to the nearest industrial Ethernet switches
Emergency exit doors on the staircase side, to be provided with dome camera, door contacts and siren. for cable calculation Signal Cable connects to the nearest Access control Panel and for Network cable calculation, dome camera's CAT6 (Indoor) cable connects to the nearest industrial Ethernet switches
1 Dedicated 15U server rack to be provided to keep the Access switches (switches port numbers based on the Number of cameras and Access control panels), Fiber patch panel, UTP patch panel, cable manager. for fibre cable calculation, single-mode fibre connectivity from the security building to the 380KV GIS Building.
132KV GIS Building:
Single entry card readers on the entry side with dome cameras, Break glass unit, Magnetic locks, Door contacts to be provided for All Doors. for cable calculation Signal Cable connects to the nearest Access control Panel and for Network cable calculation, dome camera's CAT6 (Indoor) cable connects to the nearest industrial Ethernet switches
Emergency exit doors on the staircase side, to be provided with dome camera, door contacts and siren. for cable calculation Signal Cable connects to the nearest Access control Panel and for Network cable calculation, dome camera's CAT6 (Indoor) cable connects to the nearest industrial Ethernet switches
1 Dedicated 15U server rack to be provided to keep the Access switches (switches port numbers based on the Number of cameras and Access control panels), Fiber patch panel, UTP patch panel, cable manager. for fibre cable calculation, single-mode fibre connectivity from the security building to the 132KV GIS building.
13.8KV Switchgear building:
Single entry card readers on the entry side with dome cameras, Break glass unit, Magnetic locks, Door contacts to be provided for All Doors. for cable calculation Signal Cable connects to the nearest Access control Panel and for Network cable calculation, dome camera's CAT6 (Indoor) cable connects to the nearest industrial Ethernet switches
Emergency exit doors on the staircase side, to be provided with dome camera, door contacts and siren. for cable calculation Signal Cable connects to the nearest Access control Panel and for Network cable calculation, dome camera's CAT6 (Indoor) cable connects to the nearest industrial Ethernet switches
1 Dedicated 15U server rack to be provided to keep the Access switches (switches port numbers based on the Number of cameras and Access control panels), Fiber patch panel, UTP patch panel, cable manager. for fibre cable calculation, single-mode fibre connectivity from the security building to the 13.8KV Switchgear Building.
Control building:
In and out card readers with dome cameras, Break glass unit, Magnetic locks, Door contacts to be provided for All Doors entrance of control room. for cable calculation Signal Cable connects to the nearest Access control Panel and for Network cable calculation, dome camera's CAT6 (Indoor) cable connects to the nearest industrial Ethernet switches
Emergency exit doors on the staircase side, to be provided with dome camera, door contacts and siren. for cable calculation Signal Cable connects to the nearest Access control Panel and for Network cable calculation, dome camera's CAT6 (Indoor) cable connects to the nearest industrial Ethernet switches
1 Dedicated 15U server rack to be provided to keep the Access switches (switches port numbers based on the Number of cameras and Access control panels), Fiber patch panel, UTP patch panel, cable manager. for fibre cable calculation, single-mode fibre connectivity from the security building to the Control Building.
Cable tunnel:
Single entry card readers on the entry side with dome cameras, Break glass unit, Magnetic locks, Door contacts to be provided for All Doors. for cable calculation Signal Cable connects to the nearest Access control Panel and for Network cable calculation, dome camera's CAT6 (Indoor) cable connects to the nearest industrial Ethernet switches
## Action
Create the full Bill of Quantities using the details provided above.`,

    physical_equipment: `Class-1 380 KV substations HCIS Requirements
## Role
Act as a **Senior Physical Security Estimation Engineer
Your specialization includes:
- Gate Barrier Systems
- Road Blockers
- Bollards
- Turnstiles
- Vehicle Access Control
- Under Vehicle Surveillance System (UVSS)
- Gates
Main Entrance Gate:
Motorized Sliding / Swing gate (Strong steel)
UVSS- for entry side
Gate barrier barrier- Both entry and exit side to cover the full lane
Road blocker- Both entry and exit side, 4-meter size (approx.)
Bollards- 1100mm distance from edge to edge from gate to road blocker
Speed humps- to cover the full lanes, both entry and exit side
Pedestrian Gate: (or Turnstile)
Bollards- Bollards to cover the entry area of pedestrian gate
Single leaf swing gate -1.2 meter
Gatehouse:
Road blocker control switch
Raise arm barrier control switch
Turnstile control switch
Swing gate/sliding gate control switch
Emergency Alarm Button/Panic alarm button
Outdoor siren- 2 Nos, for entry side and exit side
Preliminary Inspection checkpoint:
Raise arm barrier- To cover the full lanes
Emergency Alarm button
Tire killers- to cover the full lanes both entry and exit sides
Bollards- to cover the PIC building
Emergency Gate:
Manual Swing/Sliding gate with same anti-personnel measures
Crash rated Arm barrier (or) Hydraulic bollards- To cover the full lanes
Speed humps- to cover the full lanes
Telecom shelter: (For SEC)
Manual Swing gate (Class 4)
## Action
Create the full Bill of Quantities using the details provided above.`,

    electrical_ups: `Class-1 380 KV substations HCIS Requirements
## Role
Act as a **Senior Physical Security Estimation Engineer
Your specialization includes:
- Security Lighting
- UPS
- Electrical cable
- Generator
Perimeter:
Perimeter Lighting- 5 Meter poles, 20 meters distance
Main Entrance Gate:
Area Lightings- Area lighting to achieve 5 Lux, Entry and exit 100 meters from the gatehouse in 10-meter poles
Checkpoint lighting- On the sunshade area to achieve 100 Lux (min).
Gatehouse:
Gatehouse interior lighting- minimum 300 lux
Preliminary Inspection checkpoint:
PIC area lighting- from entry and exit 100 meters, Lux level min 5 lux
UPS load calculation:
UPS load calculation should be included with ISS server (Main and redundant), Network video recorder (Main and redundant), Core switch (Main and redundant), Access switch for all buildings, Industrial ethernet switch for All FECs, Access Control panels, Workstations and monitors, PTZ cameras (if considered separate power supply). It has to be considered with 30% spare capacity.
Some of the typical load consumption on the below.
Diesel Generator Load calculation:
Diesel Generator load calculation should include the UPS load with 30% load capacity, Road blockers, raise arm barriers, all lighting, Motorized gates, HVAC for security buildings (if provided), hydraulic bollards. It has to be provided with 20% spare capacity.
Electrical Part:
One Security Main distribution board is to be considered.
One UPS DB to be considered for essential loads.
One Electrical DB to be considered for non-essential loads. If perimeter size is more than 1500-meter 2 electrical DBs needs to be considered.
Power cables:
From Security MDB to Diesel generator 4C x 95 Sqmm
From Security MDB to Electrical DB 4C x 50 Sqmm
From Security MDB to UPS DB 4C x 50 Sqmm
From Electrical DB to all physical security 4C x 6 Sqmm
From Electrical DB to all lightings 4C x 16 Sqmm
From UPS DB to server rack 3C x 6 Sqmm
From UPS DB to FEC 4C x 10 Sqmm
From UPS DB to ACS panel 3C x 2.5 Sqmm
From UPS DB to workstation 3C x 2.5 Sqmm
## Action
Create the full Bill of Quantities using the details provided above.
Note: This prompt's results are linked to Prompt 1, Prompt 2, and Prompt 3 of Class 1 380KV Substation.`,
  },

  class3: {
    video_access: `Class-3 Smaller substation HCIS Requirements
## Role
Act as a **Senior Physical Security Estimation Engineer
Your specialization includes:
- CCTV / Video Surveillance System
- Video Management System (VMS)
- Access Control System (ACS)
- Video Intercom
- Automatic Number Plate Recognition (ANPR/LPR)
- Security Servers, Workstations and Storage
Perimeter:
External PTZ camera – Every 250 meters with 7-meter poles or to be considered for both corners diagonally.
Short range fixed camera- for each transformer (Critical assets) with 3-meter pole
External fixed camera – Maximum 75 meters distance with VA (5 Meter pole)
Main Entrance Gate:
Short Range fixed camera – one for each Lane for monitoring and one for card reader monitoring (3-meter pole)
Gate PTZ camera- One camera for Entry side. (5-meter pole)
Card Readers- Both Entry and Exit lanes (1.2-meter pole)
Video Intercom- Both Entry and Exit lanes (1.2-meter pole)
ALPR- For entry side (1.2-meter pole), with the beacon
Pedestrian Gate: (or Turnstile)
Outdoor Dome camera- Outdoor dome camera for each in and out card readers.
Card readers- for In and Out
Video Intercom – For in and out
Emergency Gate:
A dedicated fixed camera to monitor the gate
Magnetic boundary sensor for the gates
Telecom shelter: (For SEC)
Short range fixed camera – for monitoring the gate
Substation building:
In and outside card readers with dome cameras, Break glass unit, Magnetic locks, Door contacts to be provided for Battery room, communication room, Control room
Single entry card reader with dome camera, emergency break glass, push button, Magnetic locks, door contacts only provided for Switchgear room, GIS room
Door contacts to be provided for emergency doors with the Siren.
All emergency doors are equipped with fixed dome cameras.
Warehouse/workshop to be provided with door contacts.
Clean agent room/firefighting room to be provided with door contacts and one dome camera.
ISS server (Main and redundant, Server sizing based on the number of cameras), Network video recorder (Main and redundant, recorder Server sizing based on the number of cameras), Access control Server (Main and redundant) located in communication room
ISS workstation located in the communication room
ALPR workstation located in the communication room
ACS controllers with power supply to be provided.
Storage calculation:
Perimeter External PTZ camera- for continuous recording 8 Fps, 720P, 3 months, H.265
For Motion recording 30 fps, 1080P, 5%
Perimeter External fixed camera- for continuous recording 8 Fps, 720P, 1 month, H.265
For Motion recording 30 fps, 1080P, 5%
Short range fixed camera- for continuous recording 8 Fps, 720P, 3 months, H.265
For Motion recording 30 fps, 1080P, 5%
Buildings dome camera (indoor/outdoor)- for continuous recording 8 Fps, 720P, 3 months,
For Motion recording 30 fps, 1080P, 5%, H.265
Gate External PTZ camera- for continuous recording 8 Fps, 720P, 1 month, H.265
For Motion recording 30 fps, 1080P, 5%
## Action
Create the full Bill of Quantities using the details provided above.`,

    personnel_fence: `Class-3 Smaller substation HCIS Requirements
## Role
Act as a **Senior Physical Security Estimation Engineer
Your specialization includes:
- Category - 3 fence
- Fiber Optic Infrastructure
- Network cable (CAT 6) Infrastructure
- Signal Cable Infrastructure
- Security Networks
Perimeter:
Category 3 Fencing or boundary wall.
FEC cabinet- Every 150 meters on the perimeter with single-mode fibre connectivity from the Substation building communication room, it has to be provided with Industrial ethernet switches (switches port numbers based on the Number of cameras), Fiber patch panel, UTP patch panel, splicing box.
Short range fixed camera- for each transformer (Critical assets) with 3-meter pole
External PTZ camera – Every 250 meters with 7-meter poles or to be considered for both corners diagonally CAT6 (Outdoor) cable connects to the nearest Industrial Ethernet switches
Every 75 meters on perimeter one VA camera for cable calculation, CAT6 (Outdoor) cable connects to the nearest Industrial Ethernet switches
Main Entrance Gate:
Short Range fixed camera – One for each Lane for cable calculation, CAT6 (Outdoor) cable connects to the nearest the Industrial Ethernet switches
Gate PTZ camera- One camera for Entry side for cable calculation, CAT6 (Outdoor) cable connects to the nearest Industrial Ethernet switches
Card Readers- Both Entry and Exit lanes for cable calculation Signal Cable connects to the nearest Access control Panel
Video Intercom- Both Entry and Exit lanes for cable calculation, CAT6 (Outdoor) cable connects to the nearest the Industrial Ethernet switches
Pedestrian Gate: (or Turnstile)
Outdoor Dome camera- Outdoor dome camera for each in and out card readers for cable calculation, CAT6 (Outdoor) cable connects to the nearest Industrial Ethernet switches
Card readers- for In and Out for Signal Cable calculation for cable calculation Signal Cable connects to the nearest Access control Panel
Video Intercom – For in and out for cable calculation, CAT6 (Outdoor) cable connects to the nearest the Industrial Ethernet switches
Emergency Gate:
A dedicated fixed camera to monitor the gate for cable calculation, CAT6 (Outdoor) cable connects to the nearest Industrial Ethernet switches
Magnetic boundary sensor for the gates, for cable calculation, Signal Cable calculation connected to the FEC
Telecom shelter: (For SEC)
Short range fixed camera – for monitoring the gate for cable calculation, CAT6 (Outdoor) cable connects to the nearest Industrial Ethernet switches
Substation building:
In and outside card readers with dome cameras, Break glass unit, Magnetic locks, Door contacts to be provided for Battery room, communication room, Control room for cable calculation Signal Cable connects to the nearest Access control Panel and for Network cable calculation dome camera's CAT6 (Indoor) cable connects to the nearest Ethernet switches
Single entry card reader with dome camera, emergency break glass, push button, Magnetic locks, door contacts only provided for Switchgear room, GIS room for cable calculation Signal Cable connects to the nearest Access control Panel and for Network cable calculation dome camera's CAT6 (Indoor) cable connects to the nearest Ethernet switches
Door contacts to be provided for emergency doors with the Siren for cable calculation Signal Cable connects to the nearest Access control Panel
All emergency doors are equipped with fixed dome cameras for Network cable calculation CAT6 (Indoor) cable connects to the nearest Ethernet switches
Warehouse/workshop to be provided with door contacts for cable calculation Signal Cable connects to the nearest Access control Panel
Clean agent room/firefighting room to be provided with door contacts and 1 dome camera for cable calculation Signal Cable connects to the nearest Access control Panel and for Network cable calculation dome camera's CAT6 (Indoor) cable connects to the nearest Ethernet switches
2 Dedicated 42 U server rack to be provided in Communication room, to keep the Core switches (switches the port numbers based on the access switches), Access switches (switches port numbers based on the Number of cameras and Access control panels), KVM switch, Fiber patch panel, UTP patch panel, cable manager.
## Action
Create the full Bill of Quantities using the details provided above.`,

    physical_equipment: `Class-3 Smaller substation HCIS Requirements
## Role
Act as a **Senior Physical Security Estimation Engineer
Your specialization includes:
- Gate Barrier Systems
- Road Blockers
- Bollards
- Gates
Main Entrance Gate:
Motorized Sliding / Swing gate (Strong steel)
Gate barrier- entry side to cover the full lane
Road blocker- entry side, 4-meter size (approx.) on Main gate.
Bollards- 1100mm distance from edge to edge from gate to road blocker on main gate and pedestrian gate.
Speed humps- to cover the full lanes, both entry and exit side of both main gate and emergency gate.
Pedestrian Gate:
Single leaf swing gate for pedestrian gate.
Emergency Gate:
Manual Swing/Sliding Gate
Telecom shelter:
Manual Swing/Sliding Gate
## Action
Create the full Bill of Quantities using the details provided above.`,

    electrical_ups: `Class-3 Smaller substation HCIS Requirements
## Role
Act as a **Senior Physical Security Estimation Engineer
Your specialization includes:
- UPS
- Electrical cable
UPS load calculation:
UPS load calculation should be included with ISS server (Main and redundant), Network video recorder (Main and redundant), Core switch (Main and redundant), Access switch for all buildings, Industrial ethernet switch for All FECs, Access Control panels, Workstations and monitors, PTZ cameras (if considered separate power supply). It has to be considered with 30% spare capacity.
Some of the typical load consumption on the below.
Electrical Part:
One Security Main distribution board is to be considered.
One UPS DB to be considered for essential loads.
One Electrical DB to be considered for non-essential loads. If perimeter size is more than 1500-meter 2 electrical DBs needs to be considered.
Power cables:
From Security MDB to Diesel generator 4C x 95 Sqmm
From Security MDB to Electrical DB 4C x 50 Sqmm
From Security MDB to UPS DB 4C x 50 Sqmm
From Electrical DB to all physical security 4C x 6 Sqmm
From Electrical DB to all lightings 4C x 16 Sqmm
From UPS DB to server rack 3C x 6 Sqmm
From UPS DB to FEC 4C x 10 Sqmm
From UPS DB to ACS panel 3C x 2.5 Sqmm
From UPS DB to workstation 3C x 2.5 Sqmm
## Action
Create the full Bill of Quantities using the details provided above.
Note: This prompt's results are linked to Prompt 1, Prompt 2, and Prompt 3 of Class 3 Smaller Substation.`,
  },
};
