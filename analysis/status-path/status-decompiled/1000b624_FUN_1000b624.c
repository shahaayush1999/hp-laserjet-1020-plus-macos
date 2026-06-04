/* Function: 1000b624 FUN_1000b624 */


void FUN_1000b624(int param_1,undefined4 param_2)

{
  undefined4 uVar1;
  int iVar2;
  char cVar3;
  undefined *puVar4;
  
  hp1020_append_string_to_buffer_candidate(param_1,PTR_s_CODE__10006128);
  uVar1 = hp1020_status_word_to_pjl_code_candidate(param_2);
  iVar2 = hp1020_strlen_like(param_1);
  hp1020_format_into_buffer_candidate(param_1 + iVar2,PTR_DAT_10006090,uVar1);
  puVar4 = PTR_DAT_100060ec;
  hp1020_append_string_to_buffer_candidate(param_1,PTR_DAT_100060ec);
  hp1020_append_string_to_buffer_candidate(param_1,PTR_s_DISPLAY___1000612c);
  uVar1 = hp1020_datastore_lock_entry_candidate(0x1a);
  hp1020_append_string_to_buffer_candidate(param_1,uVar1);
  hp1020_append_string_to_buffer_candidate(param_1,PTR_DAT_10006130);
  hp1020_append_string_to_buffer_candidate(param_1,puVar4);
  hp1020_datastore_unlock_entry_candidate(0x1a);
  hp1020_append_string_to_buffer_candidate(param_1,PTR_s_ONLINE__10006134);
  cVar3 = hp1020_datastore_get_value_candidate(0x18);
  puVar4 = DAT_1000613c;
  if (cVar3 == '\0') {
    puVar4 = PTR_s_FALSE_10006138;
  }
  hp1020_append_string_to_buffer_candidate(param_1,puVar4);
  hp1020_append_string_to_buffer_candidate(param_1,PTR_DAT_100060ec);
  return;
}


