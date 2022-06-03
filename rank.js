Function get_rank();
Begin
    date_ :={date};
    setsysparam(pn_date(), inttodate(date_));
    setsysparam(pn_cycle(),cy_day());
    setsysparam(pn_rate(),2);
    setsysparam(pn_rateday(),inttodate(date_));

    ret := array();
    stockList_ := getbk('A股');
    StockList_::begin
        stockCode_ := mcell;
        stockName_ := stockName(stockCode_);

        if stockName_ like 'ST|退' then
            continue;

        if not (stockCode_ like 'SZ|SH') then
            continue;

        close_ := spec(close(), stockCode_);
        
        if close_ < 1.5 then
           continue;
           
        close3_ := spec(ref(close(), 3), stockCode_);
        close4_ := spec(ref(close(), 4), stockCode_);
        close5_ := spec(ref(close(), 5), stockCode_);
        close6_ := spec(ref(close(), 6), stockCode_);
        close7_ := spec(ref(close(), 7), stockCode_);
        
        if close7_ = 0 then
            continue;

        zf1 := (close_ - close3_) / close3_;
        zf2 := (close_ - close4_) / close4_;
        zf3 := (close_ - close5_) / close5_;
        zf4 := (close_ - close6_) / close6_;
        zf5 := (close_ - close7_) / close7_;

        arr1 := array(('股票名称':stockName_, '股票代码':stockCode_,
            '3日涨幅': zf1 * 100, '4日涨幅': zf2 * 100, '5日涨幅' : zf3 * 100,
            '6日涨幅': zf4 * 100, '7日涨幅': zf5 * 100));
            
        day := IntToDate(date_);
        with *,array(pn_Stock():stockCode_,PN_Date():day,pn_rate():0,pn_rateday():0) do
        begin
            timeSt := StrToTime("09:24:30");
            timeEnd := StrToTime("09:25:00")-0.00001;
            dtj:=StockDtClose(day);
            ztj:=StockZtClose(day);
            d_yclose := ref(close(), 1);

            arr2 := select  Drange(-1 to -1)
                floatn(getcol1(['buy1'],d_yclose),4)  as "竞价涨幅",
                ['buy1']  as "买一价",
                floatn(["buy1"]*["bc1"]/10000,4) as "盘口金额",
                floatn(getcol(["sale1"]=dtj,(["sc2"]+["sc1"])/["sc1"]),4) as "早盘跌停盘口比"
                from tradetable datekey day+timeSt to day+timeEnd of DefaultStockID() end;
        end
        ret &= (arr1|arr2);
    end
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
