define mycont
printf "---------------- Before -------------------\n"
!./report_kiwix-serve_memusage
finish
printf "----------------- After -------------------\n"
!./report_kiwix-serve_memusage
cont
end

define mybreak
break $arg0
commands
bt
#info reg
mycont
end
end

mybreak zim::Cluster::read

set height 0
run
