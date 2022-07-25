Function 盘口金额();
Begin
    day := {day};

    with *,array(pn_Stock():'{stock_code}',PN_Date():day,pn_rate():0,pn_rateday():0) do
    begin
        timeSt := StrToTime("09:24:30");
        timeEnd := StrToTime("09:25:00")-0.00001;
        dtj:=StockDtClose(day);
        ztj:=StockZtClose(day);
        d_yclose := ref(close(), 1);
        
        ret := select  Drange(-1 to -1)
            floatn(getcol1(['buy1'],d_yclose),4)  as "竞价涨幅",
            ['buy1']  as "买一价",
            floatn(["buy1"]*["bc1"]/10000,4) as "盘口金额",
            floatn(getcol(["sale1"]=dtj,(["sc2"]+["sc1"])/["sc1"]),4) as "早盘跌停盘口比"
            from tradetable datekey day+timeSt to day+timeEnd of DefaultStockID() end;
    end

    if not ret then
        ret := array(("竞价涨幅":0, "买一价":0, "盘口金额":0, "早盘跌停盘口比":0));
    return exportjsonstring(ret);
End;

function getcol(b_跌停,d_早盘跌停盘口比)
begin
    if b_跌停 then
        return d_早盘跌停盘口比
    else
        return 0;
end

function getcol1(d1,d2)
begin
    return (d1/d2-1)*100;
end
