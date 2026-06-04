/* Function: 1000b520 hp1020_pjl_ustatus_cancel_builder_candidate */


void hp1020_pjl_ustatus_cancel_builder_candidate(undefined4 param_1,int param_2,undefined4 param_3)

{
  undefined2 uVar1;
  undefined *puVar2;
  undefined *puVar3;
  int iVar4;
  undefined4 uVar5;
  
  puVar3 = PTR_s_USTATUS_100060e0;
  puVar2 = PTR_DAT_100060d4;
  uVar1 = *(undefined2 *)(PTR_DAT_100060dc + 4);
  *(undefined4 *)PTR_DAT_100060d4 = *(undefined4 *)PTR_DAT_100060dc;
  *(undefined2 *)(puVar2 + 4) = uVar1;
  hp1020_append_string_to_buffer_candidate(puVar2,puVar3);
  hp1020_append_string_to_buffer_candidate(puVar2,PTR_DAT_100060e4);
  hp1020_append_string_to_buffer_candidate(puVar2,PTR_DAT_10006100);
  puVar3 = PTR_DAT_100060ec;
  hp1020_append_string_to_buffer_candidate(puVar2,PTR_DAT_100060ec);
  hp1020_append_string_to_buffer_candidate(puVar2,PTR_s_CANCELED_1000611c);
  hp1020_append_string_to_buffer_candidate(puVar2,puVar3);
  if (param_2 != 0) {
    hp1020_append_string_to_buffer_candidate(puVar2,PTR_s_NAME__10006108);
    hp1020_append_string_to_buffer_candidate(puVar2,param_2);
    hp1020_append_string_to_buffer_candidate(puVar2,puVar3);
  }
  hp1020_append_string_to_buffer_candidate(puVar2,PTR_s_RESULT__10006110);
  hp1020_append_string_to_buffer_candidate(puVar2,PTR_s_USER_CANCELED_10006124);
  hp1020_append_string_to_buffer_candidate(puVar2,puVar3);
  hp1020_append_string_to_buffer_candidate(puVar2,PTR_s_PAGES__10006120);
  iVar4 = hp1020_strlen_like(puVar2);
  hp1020_format_into_buffer_candidate(puVar2 + iVar4,PTR_DAT_10006090,param_3);
  hp1020_append_string_to_buffer_candidate(puVar2,puVar3);
  hp1020_append_string_to_buffer_candidate(puVar2,PTR_DAT_100060f8);
  iVar4 = hp1020_strlen_like(puVar2);
  uVar5 = hp1020_alloc_buffer_candidate(iVar4 + 1);
  hp1020_copy_string_candidate(uVar5,puVar2);
  FUN_1000b1c4();
  FUN_1000b290(uVar5,1,param_1);
  return;
}


