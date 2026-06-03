/*
Function: 1000b3f8 hp1020_error_diag_1000b3f8
Strings:
- PARSEERROR
*/


void hp1020_error_diag_1000b3f8(undefined4 param_1,int param_2,undefined4 param_3,byte param_4)

{
  undefined2 uVar1;
  undefined *puVar2;
  int iVar3;
  undefined4 uVar4;
  undefined *puVar5;
  
  puVar5 = PTR_s_USTATUS_100060e0;
  puVar2 = PTR_DAT_100060d4;
  uVar1 = *(undefined2 *)(PTR_DAT_100060dc + 4);
  *(undefined4 *)PTR_DAT_100060d4 = *(undefined4 *)PTR_DAT_100060dc;
  *(undefined2 *)(puVar2 + 4) = uVar1;
  hp1020_append_string_to_buffer_candidate(puVar2,puVar5);
  hp1020_append_string_to_buffer_candidate(puVar2,PTR_DAT_100060e4);
  hp1020_append_string_to_buffer_candidate(puVar2,PTR_DAT_10006100);
  puVar5 = PTR_DAT_100060ec;
  hp1020_append_string_to_buffer_candidate(puVar2,PTR_DAT_100060ec);
  hp1020_append_string_to_buffer_candidate(puVar2,PTR_DAT_1000610c);
  hp1020_append_string_to_buffer_candidate(puVar2,puVar5);
  if (param_2 != 0) {
    hp1020_append_string_to_buffer_candidate(puVar2,PTR_s_NAME__10006108);
    hp1020_append_string_to_buffer_candidate(puVar2,param_2);
    hp1020_append_string_to_buffer_candidate(puVar2,puVar5);
  }
  hp1020_append_string_to_buffer_candidate(puVar2,PTR_s_RESULT__10006110);
  puVar5 = PTR_s_PARSEERROR_10006118;
  if (param_4 != 1) {
    if (param_4 < 2) {
      puVar5 = PTR_DAT_10006114;
      if (param_4 != 0) goto LAB_1000b4ab;
    }
    else {
      puVar5 = PTR_s_CANCELED_1000611c;
      if (param_4 != 2) goto LAB_1000b4ab;
    }
  }
  hp1020_append_string_to_buffer_candidate(puVar2,puVar5);
LAB_1000b4ab:
  puVar5 = PTR_DAT_100060ec;
  puVar2 = PTR_DAT_100060d4;
  hp1020_append_string_to_buffer_candidate(PTR_DAT_100060d4,PTR_DAT_100060ec);
  hp1020_append_string_to_buffer_candidate(puVar2,PTR_s_PAGES__10006120);
  iVar3 = hp1020_strlen_like(puVar2);
  hp1020_format_into_buffer_candidate(puVar2 + iVar3,PTR_DAT_10006090,param_3);
  hp1020_append_string_to_buffer_candidate(puVar2,puVar5);
  hp1020_append_string_to_buffer_candidate(puVar2,PTR_DAT_100060f8);
  iVar3 = hp1020_strlen_like(puVar2);
  uVar4 = hp1020_alloc_buffer_candidate(iVar3 + 1);
  hp1020_copy_string_candidate(uVar4,puVar2);
  FUN_1000b1c4();
  FUN_1000b290(uVar4,1,param_1);
  return;
}


