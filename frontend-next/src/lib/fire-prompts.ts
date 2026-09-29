/**
 * Fixed fire-protection BOQ prompt for substation drawings, built from the
 * client-supplied reference standard "TRANSMISSION ENGINEERING STANDARD
 * TES-P-119.21, Rev. 01 — Table 1: Types of Detecting and Actuating Means
 * and Type of Protection Systems for All Substation Voltage Levels, 380 kV
 * and Below at Various Areas" (National Grid Saudi Arabia substations).
 *
 * Unlike the security prompts (lib/security-prompts.ts), the source
 * document here is one single continuous area-by-area table rather than
 * four independently askable topics, so this is exposed as one fixed
 * prompt rather than a class/topic picker — selecting it from the chat
 * (see components/drawing-chat.tsx) sends the full requirement list below
 * verbatim, covering every area row from the standard with nothing
 * dropped, and asks the model to produce a full Bill of Quantities for
 * the fire detection/actuating devices and protection systems implied by
 * it against the actual drawing.
 */

export const FIRE_PROTECTION_PROMPT = `Fire Detection and Protection Systems and Fire Prevention Requirements
(Ref: Transmission Engineering Standard TES-P-119.21, Rev. 01, Table 1 — National Grid Saudi Arabia Substations, all voltage levels 380kV and below, Facility Classification 1, 2 and 3)
## Role
Act as a **Senior Fire Protection Estimation Engineer**
Your specialization includes:
- Fire Detection and Alarm Systems (optical, multi-sensor, heat, rate-of-rise, flame, hydrogen gas detectors)
- Clean Agent Total Flooding Systems (Novec 1230 / FM200, per SAF-04 of HCIS)
- Wet Sprinkler Systems
- CO2 and Dry Chemical Portable/Wheeled Fire Extinguishers
- Passive fire protection (fire rated walls, sump pits, fire stops, separation)
- Water Spray Fixed Systems

For each of the following areas found in the drawing, identify the required Type of Detecting and Actuating Means and the required Type of Protection System, and use them to build the Bill of Quantities:

Offices:
Detection: Fire Detection and Alarm System. A combination of optical and multi-sensors (combined optical and heat detectors) smoke detectors in 1:1 ratio.
Protection: CO2 Portable extinguishers.

Kitchen or Tea room:
Detection: Fire Detection and Alarm System. Fixed temperature rated 57°C.
Protection: CO2 Portable extinguishers.

Workshops:
Detection: Fire Detection and Alarm System. A combination of optical and multi-sensors (combined optical and heat detectors) smoke detectors in 1:1 ratio.
Protection: CO2 Portable extinguishers.

Store room:
Detection: Fire Detection and Alarm System. A combination of optical and multi-sensors (combined optical and heat detectors) smoke detectors in 1:1 ratio.
Protection: Dry chemical portable extinguishers.

Hallway, Corridor, Lobby & Stair Cases:
Detection: Fire Detection and Alarm System. A combination of optical and multi-sensors (combined optical and heat detectors) smoke detectors in 1:1 ratio.
Protection: CO2 Portable extinguishers.

GIS Hall (if any):
Detection: Fire Detection and Alarm System. A combination of optical and multi-sensors (combined optical and heat detectors) smoke detectors in 1:1 ratio. If height of the hall is above 9.0 meters, optical beam smoke detectors shall be provided.
Protection: CO2 Portable extinguishers.

Pump room (if any):
Detection: Fire Detection and Alarm System. Bulb type sprinkler rated 57°C.
Protection: Wet Sprinkler Systems and CO2 Portable extinguishers.

Oil Filled Transformer Unit:
Detection: Fire Detection and Alarm System. Actuation shall consist of cross-zoned rate of anticipation thermal heat detector, weatherproof type.
Protection: Passive fire protection systems (adequate separation, fire rated walls, sump pit, fire stops & others). Wheeled & Portable type Fire Extinguishers, class ABC, or Water Spray Fixed System if condition not met as per clause 3.8.6.5.

Oil Tank Room:
Detection: Fire Detection and Alarm System. A combination of optical and multi-sensors (combined optical and heat detectors) smoke detectors in 1:1 ratio.
Protection: CO2 portable Fire Extinguishers.

GIS room (69kV to 380kV):
Detection: Fire Detection and Alarm System. A combination of optical and multi-sensors (combined optical and heat detectors) smoke detectors in 1:1 ratio. In 69kV Air Insulated Switchgear room, each cubicle by one (1) multi-sensors (combined optical and heat detectors) smoke detector.
Protection: CO2 portable Fire Extinguishers for the room/Hall. Protect cubicle panels by an approved Clean Agent Fire Extinguishing System (UL-Listed System).

MV Switchgear rooms (13.8kV to 34.5kV):
Detection: Fire Detection and Alarm System. A combination of optical and multi-sensors (combined optical and heat detectors) smoke detectors in 1:1 ratio.
Protection: Total Flooding with an Approved Clean Agent system and CO2 portable Fire Extinguishers.

Communication room:
Detection: Fire Detection and Alarm System. A combination of optical and multi-sensors (combined optical and heat detectors) smoke detectors in 1:1 ratio.
Protection: Total Flooding with an Approved Clean Agent and CO2 portable Fire Extinguishers.

Control room:
Detection: Fire Detection and Alarm System. A combination of optical and multi-sensors (combined optical and heat detectors) smoke detectors in 1:1 ratio.
Protection: Total Flooding with an Approved Clean Agent and CO2 portable Fire Extinguishers.

Cable Entries & Basement/Tunnels (13.8kV, 33kV, 34.5kV, 110kV, 115kV, 132kV, 230kV, 380kV):
Detection: Fire Detection and Alarm System. A combination of optical and multi-sensors (combined optical and heat detectors) smoke detectors in 1:1 ratio.
Protection: Dry chemical portable Fire Extinguishers, and as per clause 3.11.

Battery Rooms:
Detection: Combination of intrinsically safe and explosion proof flame and heat detectors plus hydrogen gas detectors.
Protection: Total Flooding with an approved clean agent and CO2 portable Fire Extinguishers. Dry chemical Fire Extinguishers installed outside near the door, see clause 3.8.6.8.

HVAC Equipment (Mechanical room):
Detection: A combination of smoke and heat detectors in 1:1 ratio.
Protection: Dry chemical portable Fire Extinguishers.

HVAC Main Supply and Return Ducts:
Detection: Approved photo-optical type duct smoke detector.
Protection: (per the applicable room/area served).

AC/DC Distribution Room:
Detection: Fire Detection and Alarm System. A combination of optical and multi-sensors (combined optical and heat detectors) smoke detectors in 1:1 ratio.
Protection: Total Flooding with an Approved Clean Agent and CO2 portable Fire Extinguishers.

SCADA and Relay Rooms:
Detection: Fire Detection and Alarm System. A combination of optical and multi-sensors (combined optical and heat detectors) smoke detectors in 1:1 ratio.
Protection: Total Flooding with an Approved Clean Agent and CO2 portable Fire Extinguishers.

Toilets:
Detection: Rate of rise & fixed temperature heat detector.
Protection: Dry chemical portable Fire Extinguishers.

Security Gate Houses:
Detection: Multi-sensors (combined optical and heat detectors) or optical type of smoke detector.
Protection: Dry chemical class ABC Fire Extinguishers.

Clean Agent cylinder room:
Detection: Fire Detection and Alarm System. A combination of optical and multi-sensors (combined optical and heat detectors) smoke detectors in 1:1 ratio.
Protection: CO2 portable Fire Extinguishers.

Station Transformer:
Detection: Fire Detection and Alarm System. Adequate separation, fire rated walls, sump pit, fire stops. Weatherproof rate anticipation heat detector.
Protection: Dry chemical portable Fire Extinguishers, and as per clause 3.10.2.b.

Shunt Capacitor:
Detection: Fire Detection and Alarm System. Adequate separation, fire rated walls, sump pit, fire stops. Weatherproof rate anticipation heat detector.
Protection: Dry chemical portable Fire Extinguishers.

Shunt Reactor:
Detection: Fire Detection and Alarm System. Adequate separation, fire rated walls, sump pit, fire stops. Weatherproof rate anticipation heat detector.
Protection: Dry chemical portable Fire Extinguishers.

Record Room:
Detection: Fire Detection and Alarm System. A combination of optical and multi-sensors (combined optical and heat detectors) smoke detectors in 1:1 ratio.
Protection: Dry chemical portable Fire Extinguishers.

Note: Both Novec 1230 and FM200 are approved clean agents as per SAF-04 of HCIS.

## Action
Go through the attached drawing page by page and, for every one of the areas above that actually appears in it, list the exact detection devices and protection/extinguishing equipment shown or implied for that area (with quantities and page references where possible), then create the full Bill of Quantities using the requirements listed above as the governing specification. Flag any area from the list above that does NOT appear anywhere in the drawing, and flag any area that appears in the drawing but is not covered by the list above.`;
