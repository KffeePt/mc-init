"""Metadata extractors — resolution, format, codec, audio quality, release group."""

import re


def extract_resolution(name: str) -> str:
    """Extract video resolution from release name."""
    patterns = [
        (r'2160p|4K|UHD', "4K"),
        (r'1080p', "1080p"),
        (r'720p', "720p"),
        (r'480p|576p', "480p"),
    ]
    for pattern, label in patterns:
        if re.search(pattern, name, re.I):
            return label
    return "Unknown"


def extract_format(name: str) -> str:
    """Extract source format from release name."""
    formats = [
        (r'REMUX', "REMUX"),
        (r'BluRay|BDRip|BRRip', "BluRay"),
        (r'WEB-DL|WEBDL', "WEB-DL"),
        (r'WEBRip|WEB Rip', "WEBRip"),
        (r'HDTV|HD-TV', "HDTV"),
        (r'HDRip|HD-Rip', "HDRip"),
        (r'DVDRip|DVD-Rip', "DVDRip"),
        (r'CAM|HDTS|TELESYNC|TS', "CAM/TS"),
    ]
    for pattern, label in formats:
        if re.search(pattern, name, re.I):
            return label
    return "Unknown"


def extract_codec(name: str) -> str:
    """Extract video codec from release name."""
    codecs = [
        (r'x265|HEVC|H\.?265', "x265/HEVC"),
        (r'x264|H\.?264|AVC', "x264"),
        (r'AV1', "AV1"),
    ]
    for pattern, label in codecs:
        if re.search(pattern, name, re.I):
            return label
    return "Unknown"


def extract_audio_quality(name: str) -> str:
    """Extract audio quality from music release name."""
    qualities = [
        (r'24[_\-](96|192|88|176)\b.*\b(kHz|khz)\b', "Hi-Res"),
        (r'24bit|24[_\-]bit', "24-bit"),
        (r'FLAC', "FLAC"),
        (r'ALAC', "ALAC"),
        (r'Lossless', "Lossless"),
        (r'320\s*kbps|320k|V0', "320kbps"),
        (r'256\s*kbps|256k|V2', "256kbps"),
        (r'192\s*kbps|192k', "192kbps"),
        (r'AAC', "AAC"),
        (r'OPUS', "Opus"),
        (r'MP3', "MP3"),
    ]
    for pattern, label in qualities:
        if re.search(pattern, name, re.I):
            return label
    return "Unknown"


def extract_release_group(name: str) -> str:
    """Extract release group from name."""
    match = re.search(r'[-.]([A-Z][A-Za-z0-9]+)(?:\[|$)', name)
    if match:
        return match.group(1)
    match = re.search(r'-([A-Z]{2,10})(?:\.\w+)?$', name)
    if match:
        return match.group(1)
    return ""
