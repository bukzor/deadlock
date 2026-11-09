import ctypes

import pytest

from .convar_h import ConCommandRegList_Entry_t, ConVarRegList_Entry_t, CVarCreationBase_t, CVValue_t, offset_of
from .reglist import STRIDES
from .values import TYPES


class DescribeSizes:
    @pytest.mark.parametrize(("kind", "entry"), [("convars", ConVarRegList_Entry_t), ("concommands", ConCommandRegList_Entry_t)])
    def it_sizes_each_entry_as_its_queue_strides(self, kind: str, entry: type[ctypes.Structure]):
        assert ctypes.sizeof(entry) == STRIDES[kind]

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
