"""Per-type SMBIOS structure parser tests, exercised against captured fixtures.

Each fixture is a real-hardware DMI byte capture with serial numbers, asset
tags, and the System UUID sanitized to same-length placeholders ('A' for
strings, zero bytes for the UUID). Everything else is verbatim from the BIOS.
"""

from __future__ import annotations

import datetime

import pytest

from truenas_pydmi import enums


class TestH30Supermicro:
    """Single-socket Supermicro X12SDV / Intel Xeon-D 2796NT, SMBIOS 3.5.

    Modern firmware that exercises the Extended BIOS ROM Size path,
    SMBIOS 3.2+ memory-device fields, real cache info, IPMI, and TPM."""

    @pytest.fixture(autouse=True)
    def _setup(self, dmi_fixture):
        self.dmi = dmi_fixture("h30_supermicro")

    def test_bios(self):
        b = self.dmi.bios
        assert b.vendor == "American Megatrends International, LLC."
        assert b.version == "1.8.V2"
        assert b.release_date == datetime.date(2025, 1, 6)
        # Extended BIOS ROM Size path (legacy byte 0xFF, extended says 32 MB).
        assert b.rom_size_bytes == 32 * 1024 * 1024

    def test_bios_characteristics_decoded(self):
        names = self.dmi.bios.characteristics_decoded
        assert "PCI is supported" in names
        assert "BIOS is upgradeable" in names
        assert "UEFI is supported" in names
        assert "ACPI is supported" in names
        assert "BIOS boot specification is supported" in names

    def test_system(self):
        s = self.dmi.system
        assert s.manufacturer == "iXsystems"
        assert s.product_name == "TRUENAS-H30-HA"
        assert s.serial_number == "A" * 9
        assert s.uuid is None  # zeroed UUID -> parser treats as not-set

    def test_baseboards(self):
        bbs = self.dmi.baseboards
        assert len(bbs) == 1
        bb = bbs[0]
        assert bb.manufacturer == "Supermicro"
        assert bb.product == "X12SDV-20C-SPT8F"
        assert bb.serial_number == "A" * 12

    def test_chassis(self):
        chs = self.dmi.chassis
        assert len(chs) == 1
        c = chs[0]
        assert c.manufacturer == "Supermicro"
        assert c.type == 17
        assert enums.chassis_type_name(c.type) == "Main Server Chassis"
        assert c.power_cords == 1

    def test_processor(self):
        procs = self.dmi.processors
        assert len(procs) == 1
        p = procs[0]
        assert p.socket_designation == "CPU"
        assert p.manufacturer == "Intel(R) Corporation"
        assert p.version == "Intel(R) Xeon(R) D-2796NT CPU @ 2.00GHz"
        assert p.populated is True
        assert p.voltage_volts == 1.6
        assert p.core_count == 20
        assert p.cores_enabled == 20
        assert p.thread_count == 40
        assert p.l1_cache_handle is not None
        assert p.l2_cache_handle is not None
        assert p.l3_cache_handle is not None

    def test_caches(self):
        caches = self.dmi.caches
        assert len(caches) == 3
        l1, l2, l3 = caches
        assert l1.cache_level == 1
        assert l1.installed_size_bytes == 1638400  # 1600 KB
        assert l1.error_correction_name == "Single-bit ECC"
        assert l1.associativity_name == "8-way Set-associative"
        assert l1.location_name == "Internal"
        assert l1.enabled_at_boot is True
        assert l2.cache_level == 2
        assert l2.installed_size_bytes == 26214400  # 25 MB
        assert l3.cache_level == 3
        assert l3.installed_size_bytes == 31457280
        assert l3.associativity_name == "20-way Set-associative"

    def test_cache_lookup_by_handle(self):
        p = self.dmi.processors[0]
        l1 = self.dmi.cache_by_handle(p.l1_cache_handle)
        l2 = self.dmi.cache_by_handle(p.l2_cache_handle)
        l3 = self.dmi.cache_by_handle(p.l3_cache_handle)
        assert l1 is not None and l1.cache_level == 1
        assert l2 is not None and l2.cache_level == 2
        assert l3 is not None and l3.cache_level == 3

    def test_cache_lookup_unknown_handle(self):
        assert self.dmi.cache_by_handle(0xDEAD) is None

    def test_memory_array(self):
        arrays = self.dmi.memory_arrays
        assert len(arrays) == 1
        a = arrays[0]
        assert enums.memory_error_correction_name(a.error_correction) == "Single-bit ECC"
        assert enums.is_ecc(a.error_correction) is True
        assert a.max_capacity_bytes == 256 * 1024**3

    def test_memory_devices(self):
        devs = self.dmi.memory_devices
        assert len(devs) == 4
        for d in devs:
            assert d.populated is True
            assert d.size_bytes == 64 * 1024**3
            assert d.manufacturer == "Samsung"
            assert d.serial_number == "A" * 18
            assert enums.memory_type_name(d.type) == "DDR4"
            assert d.speed_mts == 2933
            assert d.configured_speed_mts == 2933
            # SMBIOS 3.2+ extensions
            assert d.memory_technology_name == "DRAM"
            assert "Volatile memory" in d.operating_mode_names

    def test_ipmi(self):
        devs = self.dmi.ipmi_devices
        assert len(devs) == 1
        ipmi = devs[0]
        assert enums.ipmi_interface_type_name(ipmi.interface_type) == "KCS (Keyboard Control Style)"
        assert ipmi.spec_version_major == 2
        assert ipmi.spec_version_minor == 0
        assert ipmi.i2c_slave_address_canonical == 0x10
        assert ipmi.base_address_value == 0xCA2
        assert ipmi.base_address_io_mapped is True

    def test_tpm(self):
        devs = self.dmi.tpm_devices
        assert len(devs) == 1
        tpm = devs[0]
        assert tpm.vendor_id == "IFX"
        assert tpm.spec_major == 2
        assert tpm.spec_minor == 0
        assert tpm.firmware_version == "13.11"

    def test_predicates(self):
        assert self.dmi.ecc_memory is True
        assert self.dmi.has_ipmi is True
        assert self.dmi.has_tpm is True


class TestF60Viking:
    """Single-socket Viking F60-HA / AMD EPYC 7543P, SMBIOS 3.3.

    Different BIOS vendor (Viking Enterprise Solutions, not AMI), AMD Zen
    architecture so it exercises the ``0x6B = AMD Zen`` family code, and
    a high-channel-count single-socket layout (8 DIMM slots, no TPM)."""

    @pytest.fixture(autouse=True)
    def _setup(self, dmi_fixture):
        self.dmi = dmi_fixture("f60_viking")

    def test_bios(self):
        b = self.dmi.bios
        assert b.vendor == "Viking Enterprise Solutions"
        assert b.version == "0ACSY001-MWH3LJ-15.09.00"
        assert b.release_date == datetime.date(2023, 5, 16)
        assert b.rom_size_bytes == 16 * 1024 * 1024

    def test_system(self):
        s = self.dmi.system
        assert s.manufacturer == "iXsystems"
        assert s.product_name == "TRUENAS-F60-HA"
        assert s.serial_number == "A" * 8
        assert s.uuid is None

    def test_baseboard(self):
        bbs = self.dmi.baseboards
        assert len(bbs) == 1
        bb = bbs[0]
        assert bb.manufacturer == "iXsystems"
        assert bb.product == "TRUENAS-F60-HA"
        assert bb.serial_number == "A" * 16

    def test_chassis(self):
        chs = self.dmi.chassis
        assert len(chs) == 1
        c = chs[0]
        assert c.manufacturer == "Viking Enterprise Solutions"
        assert c.serial_number == "A" * 16
        assert c.height_u == 2

    def test_amd_epyc_zen_family(self):
        """The 0x6B family code resolves to 'Zen' for this EPYC 7543P
        (Viking BIOS uses the legacy 1-byte field rather than the 16-bit
        Family 2 escape, so this exercises the spec-table lookup directly)."""
        p = self.dmi.processors[0]
        assert p.version == "AMD EPYC 7543P 32-Core Processor"
        assert p.manufacturer == "Advanced Micro Devices, Inc."
        assert p.family == 0x6B
        assert enums.processor_family_name(p.family) == "Zen"
        assert p.voltage_volts == 1.1
        assert p.core_count == 32
        assert p.thread_count == 64
        assert p.populated is True

    def test_caches(self):
        caches = self.dmi.caches
        assert len(caches) == 3
        levels = sorted(c.cache_level for c in caches)
        assert levels == [1, 2, 3]

    def test_eight_dimm_slots(self):
        """Single-socket EPYC has 8 memory channels; this Viking BIOS
        emits one Type 17 per channel."""
        devs = self.dmi.memory_devices
        assert len(devs) == 8
        for d in devs:
            assert d.populated is True
            assert d.size_bytes == 32 * 1024**3
            assert d.manufacturer == "Samsung"
            assert d.serial_number == "A" * 8
            assert enums.memory_type_name(d.type) == "DDR4"
            assert d.speed_mts == 3200

    def test_ipmi_present_no_tpm(self):
        assert self.dmi.has_ipmi is True
        assert self.dmi.has_tpm is False
        assert len(self.dmi.ipmi_devices) == 1


class TestM50SupermicroX11:
    """Dual-socket Supermicro X11 / Intel Xeon Gold 6146, SMBIOS 3.2.

    Two-socket variant — exercises per-CPU cache handle resolution,
    half-populated memory channels (8 of 16 DIMM slots used), and the
    Skylake-SP family code (``0xB3 = Intel Xeon`` per spec, distinct
    from the Xeon-D's BIOS-quirky ``0xB2 = Pentium 4``)."""

    @pytest.fixture(autouse=True)
    def _setup(self, dmi_fixture):
        self.dmi = dmi_fixture("m50_supermicro_x11")

    def test_bios(self):
        b = self.dmi.bios
        assert b.vendor == "American Megatrends Inc."
        assert b.version == "3.3aV3"
        assert b.release_date == datetime.date(2020, 12, 3)
        assert b.rom_size_bytes == 32 * 1024 * 1024

    def test_dual_socket_processors(self):
        procs = self.dmi.processors
        assert len(procs) == 2
        assert procs[0].socket_designation == "CPU1"
        assert procs[1].socket_designation == "CPU2"
        for p in procs:
            assert p.version == "Intel(R) Xeon(R) Gold 6146 CPU @ 3.20GHz"
            assert p.manufacturer == "Intel(R) Corporation"
            # Spec value 0xB3 = Xeon — this BIOS reports it correctly,
            # unlike the H30 Xeon-D where the BIOS emits 0xB2 (Pentium 4).
            assert p.family == 0xB3
            assert enums.processor_family_name(p.family) == "Xeon"
            assert p.populated is True
            assert p.voltage_volts == 1.6
            assert p.core_count == 12
            assert p.thread_count == 24

    def test_per_cpu_cache_handles_distinct(self):
        """Each socket gets its own L1/L2/L3 handle set; the by-handle
        lookup must return the right cache for the right CPU."""
        cpu1, cpu2 = self.dmi.processors
        assert cpu1.l1_cache_handle != cpu2.l1_cache_handle
        assert cpu1.l2_cache_handle != cpu2.l2_cache_handle
        assert cpu1.l3_cache_handle != cpu2.l3_cache_handle
        for p in (cpu1, cpu2):
            l1 = self.dmi.cache_by_handle(p.l1_cache_handle)
            l2 = self.dmi.cache_by_handle(p.l2_cache_handle)
            l3 = self.dmi.cache_by_handle(p.l3_cache_handle)
            assert l1 is not None and l1.cache_level == 1
            assert l2 is not None and l2.cache_level == 2
            assert l3 is not None and l3.cache_level == 3

    def test_caches(self):
        # 3 caches per CPU x 2 sockets = 6
        assert len(self.dmi.caches) == 6

    def test_memory_devices_partial_population(self):
        """16 DIMM slots reported across both sockets; this particular box
        has 9 populated (one socket has a mismatched extra DIMM). Empty
        slots keep their physical locator (e.g. ``P1-DIMMC1``) but have
        ``size_bytes == 0`` so :attr:`MemoryDevice.populated` is False."""
        devs = self.dmi.memory_devices
        assert len(devs) == 16
        populated = [d for d in devs if d.populated]
        unpopulated = [d for d in devs if not d.populated]
        assert len(populated) == 9
        assert len(unpopulated) == 7
        for d in unpopulated:
            assert d.size_bytes == 0
        for d in populated:
            assert enums.memory_type_name(d.type) == "DDR4"
            assert d.speed_mts == 2666

    def test_ipmi_present_no_tpm(self):
        assert self.dmi.has_ipmi is True
        assert self.dmi.has_tpm is False


class TestMini3xAtom:
    """iXsystems Mini-3.0-X / Intel Atom C3558, SMBIOS 3.0.

    Older firmware exercising the pre-3.1 ROM-size fallback (legacy 0xFF
    with no extended field), an Atom CPU with no L3, and absence of
    IPMI/TPM."""

    @pytest.fixture(autouse=True)
    def _setup(self, dmi_fixture):
        self.dmi = dmi_fixture("mini3x_atom")

    def test_bios(self):
        b = self.dmi.bios
        assert b.vendor == "American Megatrends Inc."
        assert b.version == "L1.42A"
        assert b.release_date == datetime.date(2019, 10, 22)
        # SMBIOS 3.0 has no extended ROM size field; legacy 0xFF means
        # ">=16 MB" so we report the floor.
        assert b.rom_size_bytes == 16 * 1024 * 1024

    def test_system(self):
        s = self.dmi.system
        assert s.manufacturer == "iXsystems"
        assert s.product_name == "FREENAS-MINI-3.0-X"
        assert s.serial_number == "A" * 8
        assert s.uuid is None

    def test_processor_no_l3(self):
        procs = self.dmi.processors
        assert len(procs) == 1
        p = procs[0]
        assert p.version == "Intel(R) Atom(TM) CPU C3558 @ 2.20GHz"
        assert p.core_count == 4
        assert p.thread_count == 4  # no SMT on this Atom
        assert p.l1_cache_handle is not None
        assert p.l2_cache_handle is not None
        assert p.l3_cache_handle is None  # 0xFFFF sentinel -> None

    def test_caches_no_l3(self):
        caches = self.dmi.caches
        assert len(caches) == 2
        assert {c.cache_level for c in caches} == {1, 2}

    def test_no_ipmi_no_tpm(self):
        assert self.dmi.has_ipmi is False
        assert self.dmi.has_tpm is False
        assert self.dmi.ipmi_devices == ()
        assert self.dmi.tpm_devices == ()


class TestQemuSeabios:
    """QEMU/KVM Q35 with SeaBIOS 1.16, SMBIOS 2.8.

    Edge cases: oldest spec version we test, pure-virtual hardware,
    no caches reported, no baseboard, no IPMI/TPM, every cache handle
    is the 'not provided' sentinel, voltage is the unknown sentinel."""

    @pytest.fixture(autouse=True)
    def _setup(self, dmi_fixture):
        self.dmi = dmi_fixture("qemu_seabios")

    def test_bios(self):
        b = self.dmi.bios
        assert b.vendor == "SeaBIOS"
        assert b.version == "1.16.3-debian-1.16.3-2"
        assert b.release_date == datetime.date(2014, 4, 1)
        # Legacy byte is 0x00 -> normal formula: (0+1) * 65536 = 64 KB.
        assert b.rom_size_bytes == 65536

    def test_bios_characteristics_seabios_quirk(self):
        """SeaBIOS sets bit 3 ('BIOS Characteristics not supported') and
        nothing else in the qword. The decoder should still surface the
        extension-byte features."""
        names = self.dmi.bios.characteristics_decoded
        assert "BIOS characteristics not supported" in names
        assert "Targeted content distribution is supported" in names

    def test_system(self):
        s = self.dmi.system
        assert s.manufacturer == "QEMU"
        assert s.product_name == "Standard PC (Q35 + ICH9, 2009)"
        assert s.serial_number == "A" * 8
        assert s.uuid is None

    def test_no_baseboards(self):
        # QEMU's standard machine doesn't emit Type 2 structures.
        assert self.dmi.baseboards == ()

    def test_four_vcpus(self):
        procs = self.dmi.processors
        assert len(procs) == 4
        for i, p in enumerate(procs):
            assert p.socket_designation == f"CPU {i}"
            assert p.manufacturer == "QEMU"
            assert p.populated is True
            assert p.voltage_volts is None  # voltage_raw == 0 (unknown)
            assert p.l1_cache_handle is None  # 0xFFFF sentinel
            assert p.l2_cache_handle is None
            assert p.l3_cache_handle is None

    def test_no_caches(self):
        assert self.dmi.caches == ()

    def test_one_dimm(self):
        devs = self.dmi.memory_devices
        assert len(devs) == 1
        d = devs[0]
        assert d.size_bytes == 8 * 1024**3
        assert d.manufacturer == "QEMU"

    def test_no_ipmi_no_tpm(self):
        assert self.dmi.has_ipmi is False
        assert self.dmi.has_tpm is False
