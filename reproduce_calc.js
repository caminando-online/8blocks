
function formatDisplayCurrency(value) {
    if (isNaN(value) || value === null) return "0,00";
    return new Intl.NumberFormat('de-DE', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

const PRICE_BACKLOG = [
  {"year": 2018, "month": 1, "change_pct": -25.36},
  {"year": 2018, "month": 2, "change_pct": 14.02},
  {"year": 2018, "month": 3, "change_pct": -36.63},
  {"year": 2018, "month": 4, "change_pct": 35.63},
  {"year": 2018, "month": 5, "change_pct": -17.56},
  {"year": 2018, "month": 6, "change_pct": -15.22},
  {"year": 2018, "month": 7, "change_pct": 21.44},
  {"year": 2018, "month": 8, "change_pct": -7.52},
  {"year": 2018, "month": 9, "change_pct": -8.17},
  {"year": 2018, "month": 10, "change_pct": -3.89},
  {"year": 2018, "month": 11, "change_pct": -37.36},
  {"year": 2018, "month": 12, "change_pct": -11.11}
];

function reproduce(innerText, overrideStr) {
    console.log(`Input: innerText="${innerText}", override="${overrideStr}"`);
    
    // Original logic
    const overrideVal = overrideStr;
    const currentVal = innerText.replace('$', '').replace(/\./g, '').replace(',', '.');
    const startPrice = parseFloat(overrideVal) || parseFloat(currentVal);
    
    console.log(`Parsed startPrice: ${startPrice}`);
    
    let currentPrice = startPrice;
    let prices = [];
    
    for (let i = 0; i < 12; i++) {
        const changePct = PRICE_BACKLOG[i].change_pct;
        currentPrice = currentPrice * (1 + changePct / 100);
        
        if (i % 12 === 11) {
            prices.push(currentPrice);
        }
    }
    
    console.log(`Year 1 Price: ${prices[0]}`);
    console.log(`Formatted: ${formatDisplayCurrency(prices[0])}`);
}

reproduce("68000.00", "");
reproduce("$ 68.000,00", "");
reproduce("68,000.00", ""); // US style
reproduce("68000", "");
