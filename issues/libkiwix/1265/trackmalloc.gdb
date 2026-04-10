set $malloc_arg_in_thread_0=0
set $malloc_arg_in_thread_1=0
set $malloc_arg_in_thread_2=0
set $malloc_arg_in_thread_3=0

define show_malloc_call_info
finish
eval "printf \"thread#%u: malloc(%%u) -> %%p\\n\", $malloc_arg_in_thread_%u, $rax", $_thread, $_thread
cont
end

break malloc
commands
eval "set $malloc_arg_in_thread_%u=%u", $_thread, $rdi
show_malloc_call_info
end

break calloc
commands
printf "thread#%u: calloc(???, ???) -> ???\n", $_thread
continue
end

break realloc
commands
printf "thread#%u: realloc(???, ???) -> ???\n", $_thread
continue
end

break free
commands
silent
printf "thread#%u: free(%p)\n", $_thread, $rax
cont
end

break __cxa_throw
commands
bt
cont
end

set height 0
run
