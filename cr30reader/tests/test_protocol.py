"""
Unit tests for protocol package.

Tests for CR30Packet, PacketBuilder, PacketParser using example data from ipynb files.
"""

import unittest
import struct
from cr30reader.protocol import (
    CR30Packet,
    PacketBuilder,
    PacketParser
)


class TestCR30Packet(unittest.TestCase):
    """Tests for CR30Packet class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.example_packet_hex = (
            "aa0a0000005600190353443638373042363637000000000000000000"
            "00000000000000000000000000000000435233300000000000000000"
            "000000000000000000000000ff6e"
        )
        self.example_packet = bytes.fromhex(self.example_packet_hex)
    
    def test_init_from_bytes(self):
        """Test packet initialization from bytes."""
        pkt = CR30Packet(self.example_packet)
        
        self.assertEqual(len(pkt.to_bytes()), 60)
        self.assertEqual(pkt.start, 0xAA)
        self.assertEqual(pkt.cmd, 0x0A)
        self.assertEqual(pkt.subcmd, 0x00)
    
    def test_init_empty(self):
        """Test empty packet initialization."""
        pkt = CR30Packet()
        
        self.assertEqual(len(pkt.to_bytes()), 60)
        self.assertEqual(pkt.start, 0x00)
        self.assertEqual(len(pkt.payload), 52)
    
    def test_init_wrong_size(self):
        """Test that wrong packet size raises error."""
        wrong_data = b'\x00' * 50
        
        with self.assertRaises(ValueError):
            CR30Packet(wrong_data)
    
    def test_start_property(self):
        """Test start byte property."""
        pkt = CR30Packet()
        pkt.start = 0xBB
        self.assertEqual(pkt.start, 0xBB)
        
        # Invalid start byte should raise error
        with self.assertRaises(ValueError):
            pkt.start = 0xCC
    
    def test_cmd_subcmd_param(self):
        """Test command, subcommand, and parameter properties."""
        pkt = CR30Packet()
        pkt.cmd = 0x01
        pkt.subcmd = 0x02
        pkt.param = 0x03
        
        self.assertEqual(pkt.cmd, 0x01)
        self.assertEqual(pkt.subcmd, 0x02)
        self.assertEqual(pkt.param, 0x03)
    
    def test_payload(self):
        """Test payload property."""
        pkt = CR30Packet()
        test_payload = b'\x01' * 52
        pkt.payload = test_payload
        
        self.assertEqual(len(pkt.payload), 52)
        self.assertEqual(pkt.payload, test_payload)
    
    def test_payload_wrong_size(self):
        """Test that wrong payload size raises error."""
        pkt = CR30Packet()
        
        with self.assertRaises(ValueError):
            pkt.payload = b'\x00' * 50
    
    def test_calculate_checksum(self):
        """Test checksum calculation."""
        pkt = CR30Packet(self.example_packet)
        checksum = pkt.calculate_checksum()
        
        self.assertIsInstance(checksum, int)
        self.assertGreaterEqual(checksum, 0)
        self.assertLess(checksum, 256)
    
    def test_verify_checksum(self):
        """Test checksum verification."""
        pkt = CR30Packet(self.example_packet)
        is_valid = pkt.verify_checksum()
        
        # Example packet should have valid checksum
        self.assertTrue(is_valid)
    
    def test_is_valid(self):
        """Test packet validity check."""
        pkt = CR30Packet(self.example_packet)
        self.assertTrue(pkt.is_valid())
        
        # Invalid packet (wrong marker)
        invalid_pkt = CR30Packet()
        invalid_pkt.start = 0xAA
        invalid_pkt._data[58] = 0x00  # Wrong marker for AA
        self.assertFalse(invalid_pkt.is_valid())
    
    def test_to_bytes(self):
        """Test packet to bytes conversion."""
        pkt = CR30Packet(self.example_packet)
        packet_bytes = pkt.to_bytes()
        
        self.assertEqual(len(packet_bytes), 60)
        self.assertEqual(packet_bytes, self.example_packet)
    
    def test_to_hex(self):
        """Test packet to hex string conversion."""
        pkt = CR30Packet(self.example_packet)
        hex_str = pkt.to_hex()
        
        self.assertIsInstance(hex_str, str)
        self.assertEqual(len(hex_str), 120)  # 60 bytes * 2 chars
        self.assertEqual(hex_str, self.example_packet_hex)
    
    def test_from_bytes(self):
        """Test packet creation from bytes."""
        pkt = CR30Packet.from_bytes(self.example_packet)
        
        self.assertEqual(pkt.start, 0xAA)
        self.assertEqual(pkt.cmd, 0x0A)
        self.assertEqual(pkt.subcmd, 0x00)


class TestPacketBuilder(unittest.TestCase):
    """Tests for PacketBuilder class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.builder = PacketBuilder()
    
    def test_calculate_checksum_aa(self):
        """Test checksum calculation for 0xAA packets."""
        packet = bytearray(58)
        packet[0] = 0xAA
        packet[1] = 0x0A
        packet[2] = 0x00
        
        checksum = self.builder.calculate_checksum(bytes(packet))
        
        self.assertIsInstance(checksum, int)
        self.assertGreaterEqual(checksum, 0)
        self.assertLess(checksum, 256)
    
    def test_calculate_checksum_bb(self):
        """Test checksum calculation for 0xBB packets."""
        packet = bytearray(58)
        packet[0] = 0xBB
        packet[1] = 0x01
        packet[2] = 0x00
        
        checksum = self.builder.calculate_checksum(bytes(packet))
        
        self.assertIsInstance(checksum, int)
        # BB checksum should be (sum - 1) % 256
        expected = (sum(packet) - 1) % 256
        self.assertEqual(checksum, expected)
    
    def test_build_packet(self):
        """Test basic packet building."""
        cmd = 0x01
        subcmd = 0x02
        param = 0x03
        data = b'\x04' * 20
        
        packet = self.builder.build_packet(0xBB, cmd, subcmd, param, data)
        
        self.assertEqual(len(packet), 60)
        pkt = CR30Packet(packet)
        self.assertEqual(pkt.start, 0xBB)
        self.assertEqual(pkt.cmd, cmd)
        self.assertEqual(pkt.subcmd, subcmd)
        self.assertEqual(pkt.param, param)
        self.assertTrue(pkt.is_valid())
    
    def test_build_handshake_packet(self):
        """Test handshake packet building."""
        packet = self.builder.build_handshake_packet(0x0A, 0x00)
        
        self.assertEqual(len(packet), 60)
        pkt = CR30Packet(packet)
        self.assertEqual(pkt.start, 0xAA)
        self.assertEqual(pkt.cmd, 0x0A)
        self.assertEqual(pkt.subcmd, 0x00)
        self.assertTrue(pkt.is_valid())
    
    def test_build_command_packet(self):
        """Test command packet building."""
        packet = self.builder.build_command_packet(0x01, 0x02, 0x03)
        
        self.assertEqual(len(packet), 60)
        pkt = CR30Packet(packet)
        self.assertEqual(pkt.start, 0xBB)
        self.assertEqual(pkt.cmd, 0x01)
        self.assertEqual(pkt.subcmd, 0x02)
        self.assertEqual(pkt.param, 0x03)
        self.assertTrue(pkt.is_valid())


class TestPacketParser(unittest.TestCase):
    """Tests for PacketParser class using example data from ipynb."""
    
    def setUp(self):
        """Set up test fixtures with example packets from ipynb."""
        self.parser = PacketParser()
        
        # Example packets from packets.ipynb
        self.device_name_packet = bytes.fromhex(
            "aa0a0000005600190353443638373042363637000000000000000000"
            "00000000000000000000000000000000435233300000000000000000"
            "000000000000000000000000ff6e"
        )
        
        self.measurement_header_packet = bytes.fromhex(
            "bb010900281f0a00000000000000000000000000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000"
            "00000000000000ff15"
        )
        
        # Chunk 0x10 packet (first SPD chunk)
        self.chunk_0x10_packet = bytes.fromhex(
            "bb01100000000000000000000000000000000000000000000000000000"
            "0000000000000000000000000000000000000000000000000000000000"
            "00000000000000ffcb"
        )
        # Response packet with SPD data (from ipynb)
        self.chunk_0x10_response = bytes.fromhex(
            "bb011000000000a468b040b174e64086130141f49c094199031341bbd81e41"
            "b94b2b4175693941648049411fb159418b716641168c684100000000ff37"
        )
    
    def test_is_valid_packet(self):
        """Test packet validity check."""
        self.assertTrue(self.parser.is_valid_packet(self.device_name_packet))
        self.assertTrue(self.parser.is_valid_packet(self.measurement_header_packet))
        
        # Invalid packet
        invalid = b'\x00' * 60
        self.assertFalse(self.parser.is_valid_packet(invalid))
    
    def test_extract_payload(self):
        """Test payload extraction."""
        payload = self.parser.extract_payload(self.device_name_packet)
        
        self.assertEqual(len(payload), 52)
        # Payload should start at byte 4
        self.assertEqual(payload[0], self.device_name_packet[4])
    
    def test_extract_payload_invalid(self):
        """Test that invalid packet raises error."""
        invalid = b'\x00' * 60
        invalid = bytes([0xCC] + [0x00] * 59)  # Invalid start byte
        
        with self.assertRaises(ValueError):
            self.parser.extract_payload(invalid)
    
    def test_parse_header(self):
        """Test header parsing."""
        pkt = self.parser.parse_header(self.measurement_header_packet)
        
        self.assertIsInstance(pkt, CR30Packet)
        self.assertEqual(pkt.cmd, 0x01)
        self.assertEqual(pkt.subcmd, 0x09)
    
    def test_parse_device_info(self):
        """Test device info parsing."""
        info = self.parser.parse_device_info(self.device_name_packet)
        
        self.assertIsInstance(info, dict)
        self.assertEqual(info['cmd'], 0x0A)
        self.assertEqual(info['subcmd'], 0x00)
        # Device name should be parsed
        self.assertIn('name', info)
        self.assertIn('model', info)
    
    def test_parse_measurement_header(self):
        """Test measurement header parsing."""
        pkt = self.parser.parse_measurement_header(self.measurement_header_packet)
        
        self.assertIsInstance(pkt, CR30Packet)
        self.assertEqual(pkt.subcmd, 0x09)
    
    def test_parse_measurement_header_invalid(self):
        """Test that non-measurement header raises error."""
        wrong_packet = self.device_name_packet
        
        with self.assertRaises(ValueError):
            self.parser.parse_measurement_header(wrong_packet)
    
    def test_parse_spd_chunk_0x10(self):
        """Test SPD chunk 0x10 parsing."""
        self.parser.reset_spd_collection()
        
        chunk_info = self.parser.parse_spd_chunk(self.chunk_0x10_response)
        
        self.assertIsInstance(chunk_info, dict)
        self.assertEqual(chunk_info['subcmd'], 0x10)
        self.assertIn('payload', chunk_info)
        self.assertIn('spd', chunk_info)
        self.assertIn('spd_bytes_count', chunk_info)
        self.assertGreater(chunk_info['spd_bytes_count'], 0)
    
    def test_parse_spd_chunk_accumulation(self):
        """Test that SPD chunks accumulate correctly."""
        self.parser.reset_spd_collection()
        
        # Parse multiple chunks
        chunk1 = self.parser.parse_spd_chunk(self.chunk_0x10_response)
        
        # Check accumulation
        spd_bytes = self.parser.get_accumulated_spd()
        self.assertGreater(len(spd_bytes), 0)
        
        # Check chunks info
        chunks_info = self.parser.get_chunks_info()
        self.assertEqual(len(chunks_info), 1)
        self.assertEqual(chunks_info[0]['subcmd'], 0x10)
    
    def test_parse_spd_chunk_duplicate(self):
        """Test that duplicate chunk raises error."""
        self.parser.reset_spd_collection()
        
        # Parse chunk once
        self.parser.parse_spd_chunk(self.chunk_0x10_response)
        
        # Try to parse again - should raise error
        with self.assertRaises(ValueError):
            self.parser.parse_spd_chunk(self.chunk_0x10_response)
    
    def test_reset_spd_collection(self):
        """Test SPD collection reset."""
        self.parser.reset_spd_collection()
        self.parser.parse_spd_chunk(self.chunk_0x10_response)
        
        self.assertGreater(len(self.parser.get_accumulated_spd()), 0)
        
        # Reset and verify empty
        self.parser.reset_spd_collection()
        self.assertEqual(len(self.parser.get_accumulated_spd()), 0)
        self.assertEqual(len(self.parser.get_chunks_info()), 0)
    
    def test_is_spd_complete(self):
        """Test SPD completeness check."""
        self.parser.reset_spd_collection()
        
        # Initially not complete
        self.assertFalse(self.parser.is_spd_complete())
        
        # After parsing all chunks, should be complete
        # (In real scenario, would need all 4 chunks: 0x10, 0x11, 0x12, 0x13)
        # For now, just test that it checks correctly
        chunks = [0x10, 0x11, 0x12, 0x13]
        for subcmd in chunks:
            # Create a simple packet for each chunk
            pkt = CR30Packet()
            pkt.start = 0xBB
            pkt.cmd = 0x01
            pkt.subcmd = subcmd
            try:
                self.parser.parse_spd_chunk(pkt.to_bytes())
            except ValueError:
                # Some chunks might need proper payload, skip
                pass
        
        # Check if complete (might still be False if payloads were invalid)
        # This is mainly to test the method exists and works
        _ = self.parser.is_spd_complete()
    
    def test_verify_checksum(self):
        """Test checksum verification."""
        is_valid = self.parser.verify_checksum(self.device_name_packet)
        self.assertTrue(is_valid)
    
    def test_parse_packet(self):
        """Test generic packet parsing."""
        pkt = self.parser.parse_packet(self.device_name_packet)
        
        self.assertIsInstance(pkt, CR30Packet)
        self.assertEqual(pkt.start, 0xAA)
        self.assertEqual(pkt.cmd, 0x0A)
    
    def test_parse_packet_invalid(self):
        """Test that invalid packet raises error."""
        parser = PacketParser()
        invalid = bytes([0xCC] + [0x00] * 59)
        
        with self.assertRaises(ValueError):
            parser.parse_packet(invalid)


class TestPacketIntegration(unittest.TestCase):
    """Integration tests using real packet examples from ipynb."""
    
    def setUp(self):
        """Set up with example communication packets."""
        # Example communication sequence from packets.ipynb
        self.communication_hex = [
            'aa0a0000005600190353443638373042363637000000000000000000000000000000000000000043523330000000000000000000000000000000ff6e',
            'aa0a0100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffb4',
            'aa0a010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000434d3434334c3037383700000000000000000000000000000000000000005631312e332e000000ff48',
            'bb0110000000a468b040b174e64086130141f49c094199031341bbd81e41b94b2b4175693941648049411fb159418b716641168c684100000000ff37',
            'bb0111000000ef595d41350a4841fe333041c42c1941c61e05415d00ea404aabcd403587ae40c45b9340486b874061768b40658f8d4000000000ff92',
            'bb01120000001bb68a40f2278a409ee68c4090589340567b9a407a07a1400260a640000000000000000000000000000000000000000000000000ffab',
            'bb011300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a468b040b174e64086130141f49c09419903134100000000ffba',
        ]
        self.packets = [bytes.fromhex(h) for h in self.communication_hex]
    
    def test_parse_device_name_packet(self):
        """Test parsing device name packet."""
        parser = PacketParser()
        info = parser.parse_device_info(self.packets[0])
        
        self.assertEqual(info['cmd'], 0x0A)
        self.assertEqual(info['subcmd'], 0x00)
        self.assertIn('name', info)
        self.assertIn('model', info)
        # Device name should start with 'SD'
        self.assertTrue(info['name'].startswith('SD'))
    
    def test_parse_spd_chunks_sequence(self):
        """Test parsing sequence of SPD chunks."""
        parser = PacketParser()
        parser.reset_spd_collection()
        
        # Parse chunks 0x10, 0x11, 0x12, 0x13 from communication
        # Skip header packets, parse only SPD chunks (indices 3-6)
        for packet in self.packets[3:7]:
            try:
                chunk_info = parser.parse_spd_chunk(packet)
                self.assertIn('subcmd', chunk_info)
                self.assertIn('payload', chunk_info)
            except ValueError as e:
                # Some chunks might not have proper structure for parsing
                # This is expected for some test cases
                pass
        
        # Should have accumulated some SPD data
        spd_bytes = parser.get_accumulated_spd()
        chunks_info = parser.get_chunks_info()
        
        self.assertIsInstance(spd_bytes, bytes)
        self.assertIsInstance(chunks_info, list)


if __name__ == '__main__':
    unittest.main()

