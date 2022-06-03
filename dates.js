Function dates();
Begin
    date_ := {day};
    arr := array();
    SetSysParam(PN_Stock(),'SH000001');
    setsysparam(pn_cycle(),cy_day());
    EndT:=inttodate(date_);
    for i := 0 to 99 do
    begin
        dd := StockEndTPrevNDay(EndT, i);
        arr &= array(('date':DateToInt(dd), 'datestr':DateToStr(dd)));
    end
    return exportjsonstring(arr);
End;
