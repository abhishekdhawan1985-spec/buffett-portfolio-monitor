const express = require('express');
const cors = require('cors');
const fetch = require('node-fetch');

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

let cache = {
  data: null,
  timestamp: null,
  ttl: 3600000
};

app.get('/api/filings', async (req, res) => {
  try {
    if (cache.data && cache.timestamp && (Date.now() - cache.timestamp < cache.ttl)) {
      return res.json(cache.data);
    }

    const response = await fetch(
      'https://data.sec.gov/submissions/CIK0001067983.json',
      {
        headers: {
          'User-Agent': 'Buffett Portfolio Monitor contact@youremail.com',
          'Accept-Encoding': 'gzip, deflate',
          'Host': 'data.sec.gov'
        }
      }
    );

    if (!response.ok) {
      throw new Error(`SEC API returned ${response.status}`);
    }

    const data = await response.json();
    const filingData = data.filings.recent;
    const form13F = [];
    
    for (let i = 0; i < filingData.form.length; i++) {
      if (filingData.form[i] === '13F-HR' || filingData.form[i] === '13F-HR/A') {
        form13F.push({
          form: filingData.form[i],
          filingDate: filingData.filingDate[i],
          reportDate: filingData.reportDate[i],
          accessionNumber: filingData.accessionNumber[i],
          url: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001067983&type=13F`
        });
        if (form13F.length >= 8) break;
      }
    }

    const result = {
      companyName: data.name,
      cik: data.cik,
      filings: form13F,
      fetchedAt: new Date().toISOString()
    };

    cache.data = result;
    cache.timestamp = Date.now();
    res.json(result);
    
  } catch (error) {
    res.status(500).json({ 
      error: 'Failed to fetch SEC data',
      message: error.message 
    });
  }
});

app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString()
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Backend API running on port ${PORT}`);
});