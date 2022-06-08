Function get_rank();
Begin
    date_ :={date};
    day := IntToDate(date_);
    setsysparam(pn_cycle(),cy_day());
    setsysparam(pn_rate(),2);
    setsysparam(pn_rateday(),day);

    ret := array();
    stockList_ := getbk('A股');
    StockList_::begin
        stockCode_ := mcell;
        stockName_ := stockName(stockCode_);

        if stockName_ like 'ST|退' then
            continue;

        if not (stockCode_ like 'SZ|SH') then
            continue;

        if not spec(IsTradeDay(IntToDate(date_)), stockCode_) then
            continue;

        SetSysParam(PN_Stock(), stockCode_);
        SetSysParam(pn_date(), StockEndTPrevNDay(day, 1));

        close_ := close();

        if close_ < 1.5 then
           continue;

        close3_ := ref(close(), 3);
        close4_ := ref(close(), 4);
        close5_ := ref(close(), 5);
        close6_ := ref(close(), 6);
        close7_ := ref(close(), 7);

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
            
        ret &= arr1;
    end
    return exportjsonstring(ret);
End;
