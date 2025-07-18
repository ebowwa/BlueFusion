#!/usr/bin/env python3
"""
Influences and Inspirations wiki content
"""

CONTENT = """# Influences and Inspirations

BlueFusion draws inspiration from several industry-leading tools in the network analysis and reverse engineering space. These tools have shaped our approach to BLE analysis and monitoring.

## Wireshark
The world's foremost network protocol analyzer, Wireshark has set the standard for packet analysis tools. Its comprehensive protocol dissection, filtering capabilities, and visual presentation of network traffic serve as inspiration for BlueFusion's packet analysis features. We aim to bring similar depth and usability specifically to the BLE domain.

## nRF Connect
Nordic Semiconductor's nRF Connect suite provides powerful tools for Bluetooth development and debugging. Their approach to BLE device scanning, service discovery, and characteristic interaction has influenced our design decisions in creating an intuitive interface for BLE exploration. The real-time monitoring capabilities and detailed GATT exploration features in BlueFusion echo the accessibility that nRF Connect brings to BLE development.

## ImHex
ImHex is a free, open-source hex editor designed for reverse engineers and programmers who need to inspect, decode, and manipulate binary data. Developed by WerWolv, it's cross-platform, running on Windows, macOS, Linux, and even in the browser. ImHex is particularly notable for its advanced analysis capabilities, including a custom pattern language, integrated disassembler, and a node-based data processor.

### Key ImHex Features That Inspire BlueFusion:

#### Pattern Language
ImHex features a custom C++-like pattern language that allows users to define and highlight data structures within binary files. This language supports complex constructs such as structs, unions, enums, bitfields, and conditionals, facilitating the reverse engineering of undocumented file formats. This approach influences our packet parsing and protocol analysis capabilities.

#### Data Inspector
The tool interprets selected bytes as various data types, including signed/unsigned integers, floats, strings, GUIDs, and timestamps. This multi-format interpretation approach guides our packet data visualization features.

#### Visual Data Processing
ImHex's node-based data processor provides a visual interface for preprocessing data before display. Users can create pipelines to decrypt, decompress, or transform data using customizable nodes - an approach we adapt for BLE packet analysis workflows.

#### Real-time Analysis
Like ImHex's entropy visualization and pattern detection, BlueFusion aims to provide real-time insights into BLE traffic patterns, helping identify encrypted regions, data structures, and protocol anomalies.

## Shared Philosophy

These tools share common principles that guide BlueFusion's development:
- **Accessibility**: Making complex analysis accessible to both beginners and experts
- **Extensibility**: Supporting custom analysis through patterns, filters, and plugins
- **Visual Clarity**: Presenting data in multiple formats for different analysis needs
- **Performance**: Handling large amounts of data efficiently
- **Community-Driven**: Building tools that serve real-world reverse engineering and security research needs

By combining the packet analysis excellence of Wireshark, the BLE-specific features of nRF Connect, and the binary analysis capabilities of ImHex, BlueFusion aims to create a comprehensive BLE analysis platform that serves the needs of security researchers, reverse engineers, and BLE developers.
"""