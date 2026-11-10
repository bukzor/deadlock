import ctypes

import pytest

from .convar_h import ConCommandRegList_Entry_t, ConVarRegList_Entry_t, CVarCreationBase_t, CVValue_t, offset_of
from .values import TYPES


class DescribeSizes:
    @pytest.mark.parametrize(("entry", "size"), [(ConVarRegList_Entry_t, 160), (ConCommandRegList_Entry_t, 64)])
    def it_sizes_each_entry_as_its_queues_measure_it(self, entry: type[ctypes.Structure], size: int):
        """The queues' strides (6848, 6851) and their blocks' allocation sizes,
        `16 + 100 * size` bytes (6860)."""
        assert ctypes.sizeof(entry) == size

    def it_sizes_the_creation_base_as_three_qwords(self):
        assert ctypes.sizeof(CVarCreationBase_t) == 24

    def it_sizes_a_value_as_the_largest_type(self):
        assert ctypes.sizeof(CVValue_t) == max(TYPES.values()) == 16


class DescribeOffsets:
    @pytest.mark.parametrize(
        ("path", "at"),
        [
            ("m_Info.m_pszName", 0),
            ("m_Info.m_pszHelpString", 8),
            ("m_Info.m_nFlags", 16),
            ("m_Info.m_valueInfo.m_Version", 24),
            ("m_Info.m_valueInfo.m_bHasDefault", 28),
            ("m_Info.m_valueInfo.m_bHasMin", 29),
            ("m_Info.m_valueInfo.m_bHasMax", 30),
            ("m_Info.m_valueInfo.m_defaultValue", 31),
            ("m_Info.m_valueInfo.m_minValue", 47),
            ("m_Info.m_valueInfo.m_maxValue", 63),
            ("m_Info.m_valueInfo.m_fnProviderCallBack", 80),
            ("m_Info.m_valueInfo.m_fnGetEnumInfoHandle", 112),
            ("m_Info.m_valueInfo.m_eVarType", 120),
            ("m_Info.m_valueInfo.m_CompletionCallBack.m_fnCompletionCallback", 128),
            ("m_Info.m_valueInfo.m_CompletionCallBack.m_bIsInterface", 136),
            ("m_pConVar", 144),
            ("m_pConVarData", 152),
        ],
    )
    def it_places_each_convar_field_where_the_registry_fit_found_it(self, path: str, at: int):
        assert offset_of(ConVarRegList_Entry_t, path) == at

    @pytest.mark.parametrize(
        ("path", "at"),
        [
            ("m_Info.m_pszName", 0),
            ("m_Info.m_pszHelpString", 8),
            ("m_Info.m_nFlags", 16),
            ("m_Info.m_CBInfo.m_fnCommandCallback", 24),
            ("m_Info.m_CBInfo.m_bIsInterface", 32),
            ("m_Info.m_CompletionCBInfo.m_fnCompletionCallback", 40),
            ("m_Info.m_CompletionCBInfo.m_bIsInterface", 48),
            ("m_Command", 56),
        ],
    )
    def it_places_each_command_field_as_measured(self, path: str, at: int):
        assert offset_of(ConCommandRegList_Entry_t, path) == at
