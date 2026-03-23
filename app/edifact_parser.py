"""EDIFACT Parser for German health insurance carrier data (.ke0 files) using pydifact"""
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
from pydifact.segmentcollection import Interchange


@dataclass
class HealthInsuranceCarrier:
    """Represents a health insurance carrier from EDIFACT data"""
    ik_number: str  # Institutionskennzeichen (9 digits)
    carrier_type: str  # e.g., "99"
    name: str
    bkk_code: str
    valid_from: Optional[datetime]
    function_code: str  # 01=new, 02=changed, 03=deleted
    acceptance_center_ik: Optional[str]  # IK of the data acceptance center
    processing_code: Optional[str]
    address_type: Optional[str]
    postal_code: Optional[str]
    city: Optional[str]
    street: Optional[str]
    message_number: str


class EdifactParser:
    """Parser for EDIFACT .ke0 files containing health insurance carrier data"""

    def __init__(self, encoding: str = 'iso-8859-1'):
        self.encoding = encoding

    def parse_file(self, filepath: str) -> List[HealthInsuranceCarrier]:
        """Parse an EDIFACT .ke0 file and return list of carriers"""
        interchange = Interchange.from_file(filepath, encoding=self.encoding)
        return self._parse_interchange(interchange)

    def parse_str(self, content: str) -> List[HealthInsuranceCarrier]:
        """Parse EDIFACT content string"""
        interchange = Interchange.from_str(content)
        return self._parse_interchange(interchange)

    def _parse_interchange(self, interchange: Interchange) -> List[HealthInsuranceCarrier]:
        """Parse an EDIFACT interchange and extract carriers"""
        carriers = []

        for message in interchange.get_messages():
            carrier = self._parse_message(message.segments)
            if carrier:
                carriers.append(carrier)

        return carriers

    def _parse_message(self, segments) -> Optional[HealthInsuranceCarrier]:
        """Parse message segments into a carrier object"""
        data = {
            'ik_number': None,
            'carrier_type': None,
            'name': None,
            'bkk_code': None,
            'valid_from': None,
            'function_code': None,
            'acceptance_center_ik': None,
            'processing_code': None,
            'address_type': None,
            'postal_code': None,
            'city': None,
            'street': None,
            'message_number': None
        }

        for segment in segments:
            tag = segment.tag
            elements = segment.elements

            if tag == 'UNH':
                # UNH+00001+KOTR:02:001:KV
                if len(elements) > 0:
                    data['message_number'] = str(elements[0])

            elif tag == 'IDK':
                # IDK+100167999+99+DAK+78602
                # or IDK+661430046+99+DAVASO GmbH (no BKK code)
                if len(elements) >= 3:
                    data['ik_number'] = str(elements[0])
                    data['carrier_type'] = str(elements[1])
                    data['name'] = str(elements[2])
                    if len(elements) >= 4:
                        data['bkk_code'] = str(elements[3])

            elif tag == 'VDT':
                # VDT+19951001
                if len(elements) >= 1:
                    date_str = str(elements[0])
                    if len(date_str) == 8:
                        try:
                            data['valid_from'] = datetime.strptime(date_str, '%Y%m%d')
                        except ValueError:
                            pass

            elif tag == 'FKT':
                # FKT+01
                if len(elements) >= 1:
                    data['function_code'] = str(elements[0])

            elif tag == 'VKG':
                # VKG+01+105830016+5++++++00
                # This is the critical segment linking to acceptance center
                if len(elements) >= 2:
                    data['processing_code'] = str(elements[0])
                    data['acceptance_center_ik'] = str(elements[1])

            elif tag == 'NAM':
                # NAM+01+DAK-Gesundheit
                # or NAM+01+Hamburg Münchener+Krankenkasse
                if len(elements) >= 1:
                    # Join all elements as the name might be split
                    name_parts = [str(e) for e in elements[1:]] if len(elements) > 1 else [str(elements[0])]
                    full_name = ' '.join(name_parts)
                    # Only update if we don't have a name from IDK or if this is longer
                    if not data['name'] or len(full_name) > len(data['name']):
                        data['name'] = full_name

            elif tag == 'ANS':
                # ANS+1+20097+Hamburg+Nagelsweg 27-31
                # or ANS+2+30125+Hannover (no street)
                if len(elements) >= 3:
                    data['address_type'] = str(elements[0])
                    data['postal_code'] = str(elements[1])
                    data['city'] = str(elements[2])
                    if len(elements) >= 4:
                        data['street'] = str(elements[3])

        # Only create carrier if we have essential data
        if data['ik_number'] and data['name']:
            return HealthInsuranceCarrier(
                ik_number=data['ik_number'],
                carrier_type=data['carrier_type'] or '',
                name=data['name'],
                bkk_code=data['bkk_code'] or '',
                valid_from=data['valid_from'],
                function_code=data['function_code'] or '',
                acceptance_center_ik=data['acceptance_center_ik'],
                processing_code=data['processing_code'],
                address_type=data['address_type'],
                postal_code=data['postal_code'],
                city=data['city'],
                street=data['street'],
                message_number=data['message_number'] or ''
            )

        return None


if __name__ == '__main__':
    # Test the parser
    import sys

    if len(sys.argv) > 1:
        parser = EdifactParser()
        carriers = parser.parse_file(sys.argv[1])

        print(f"Parsed {len(carriers)} carriers:\n")
        for carrier in carriers[:10]:  # Show first 10
            print(f"IK: {carrier.ik_number}")
            print(f"Name: {carrier.name}")
            print(f"City: {carrier.city}")
            print(f"Acceptance Center IK: {carrier.acceptance_center_ik}")
            print("-" * 60)
    else:
        print("Usage: python edifact_parser.py <file.ke0>")
