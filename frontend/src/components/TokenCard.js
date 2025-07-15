import React from 'react';
import moment from 'moment';

const TokenCard = ({ token }) => {
  const getStatusClass = (status) => {
    switch (status) {
      case 'PENDING':
        return 'status-pending';
      case 'ANALYZING':
        return 'status-analyzing';
      case 'COMPLETED':
        return 'status-completed';
      case 'FAILED':
        return 'status-failed';
      default:
        return 'status-pending';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'PENDING':
        return '等待分析';
      case 'ANALYZING':
        return '分析中';
      case 'COMPLETED':
        return '分析完成';
      case 'FAILED':
        return '分析失败';
      default:
        return '未知状态';
    }
  };

  const getRiskLevelClass = (level) => {
    if (level <20) {
      return 'risk-low'
    } else if (level < 60) {
      return 'risk-medium'
    } else if (level < 80) {
      return 'risk-high'
    } else {
      return 'risk-critical'
    }

  };

  const formatNumber = (num) => {
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
    return num.toString();
  };

  const analysis = token.analysisResult;

  return (
    <div className="token-card">
      <div className="token-header">
        <div className="token-info">
          <h3>{token.name}</h3>
          <p>${token.symbol}</p>
          <p className="token-mint">{token.mint.substring(0, 8)}...</p>
        </div>
        <div className={`token-status ${getStatusClass(token.analysisStatus)}`}>
          {getStatusText(token.analysisStatus)}
        </div>
      </div>

      {token.analysisStatus === 'ANALYZING' && (
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${token.analysisProgress}%` }}
          ></div>
        </div>
      )}

      <div className="token-details">
        <p><strong>创建时间:</strong> {token.created_at}</p>
        <p><strong>总供应量:</strong> {formatNumber(token.token_total_supply)}</p>
        <p><strong>虚拟SOL储备:</strong> {formatNumber(token.virtual_sol_reserves)}</p>
      </div>

       {analysis && token.analysisStatus === 'COMPLETED' && (
        <div className="analysis-content">
          {analysis.narrative_analysis && (
            <div className="analysis-section">
              <h4>叙事分析</h4>
              <p>{analysis.narrative_analysis}</p>
            </div>
          )}

          {analysis.risk_assessment && (
            <div className="analysis-section">
              <h4>风险评估</h4>
              <p>
                <strong>风险等级:</strong> 
                <span className={`risk-level ${getRiskLevelClass(analysis.risk_assessment)}`}>
                  {getRiskLevelClass(analysis.risk_assessment)}
                </span>
                <span style={{ marginLeft: '10px' }}>
                  ({analysis.risk_assessment}/100)
                </span>
              </p>
            </div>
          )}

          {analysis.market_analysis && (
            <div className="analysis-section">
              <h4>市场分析</h4>
              <p><strong>价格预测:</strong> {analysis.market_analysis}</p>
            </div>
          )}

          {analysis.ai_summary && (
            <div className="analysis-section">
              <h4>AI总结</h4>
              <p>{analysis.ai_summary}</p>
            </div>
          )}

          {analysis.investment_recommendation && (
            <div className="analysis-section">
              <h4>投资建议</h4>
              <p>{analysis.investment_recommendation}</p>
            </div>
          )}

          {analysis.web_search_results && analysis.web_search_results.length > 0 && (
            <div className="analysis-section">
             <h4 style={{ marginBottom: '10px' }}>推特搜索</h4>
              {
                analysis.tweet_result.slice(0, 3).map((result, index) => (
                  <div
                    key={index}
                    style={{
                      marginBottom: '10px',
                      border: '1px solid #eee',
                      padding: '10px',
                      borderRadius: '4px',
                      backgroundColor: '#f9f9f9',
                    }}
                  >
                    <p style={{ fontSize: '0.9rem', color: '#333', marginBottom: '5px' }}>
                      {result.content}
                    </p>
                    <a
                      href={result.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        color: '#1DA1F2', // Twitter 品牌色
                        textDecoration: 'none',
                        fontWeight: 'bold',
                        fontSize: '0.85rem',
                      }}
                    >
                      查看推文
                    </a>
                  </div>
                ))
              }
              <hr style={{ margin: '20px 0', border: 'none', borderTop: '1px solid #ddd' }} />
              <h4 style={{ marginBottom: '10px' }}>Google 搜索</h4>
              {
                analysis.web_search_results.slice(0, 3).map((result, index) => (
                  <div key={index} style={{ marginBottom: '10px' }}>
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        color: '#00d4ff',
                        textDecoration: 'none',
                        fontWeight: 'bold',
                        fontSize: '0.9rem',
                      }}
                    >
                      {result.title}
                    </a>
                    <p style={{ fontSize: '0.8rem', color: '#666', marginTop: '2px' }}>
                      {result.snippet}
                    </p>
                  </div>
                ))
              }
            </div>
          )}
        </div>
      )}

      {analysis && token.analysisStatus === 'COMPLETED_FULL' && (
        <div className="analysis-content">
          {analysis.narrative_analysis && (
            <div className="analysis-section">
              <h4>叙事分析</h4>
              <p><strong>类别:</strong> {analysis.narrative_analysis.category}</p>
              <p><strong>相关性:</strong> {analysis.narrative_analysis.relevance_score}%</p>
              <p>{analysis.narrative_analysis.description}</p>
            </div>
          )}

          {analysis.risk_assessment && (
            <div className="analysis-section">
              <h4>风险评估</h4>
              <p>
                <strong>风险等级:</strong> 
                <span className={`risk-level ${getRiskLevelClass(analysis.risk_assessment.level)}`}>
                  {analysis.risk_assessment.level}
                </span>
                <span style={{ marginLeft: '10px' }}>
                  ({analysis.risk_assessment.score}/100)
                </span>
              </p>
              <p>{analysis.risk_assessment.description}</p>
            </div>
          )}

          {analysis.market_analysis && (
            <div className="analysis-section">
              <h4>市场分析</h4>
              <p><strong>流动性:</strong> {analysis.market_analysis.liquidity_analysis}</p>
              <p><strong>价格预测:</strong> {analysis.market_analysis.price_prediction}</p>
            </div>
          )}

          {analysis.ai_summary && (
            <div className="analysis-section">
              <h4>AI总结</h4>
              <p>{analysis.ai_summary}</p>
            </div>
          )}

          {analysis.investment_recommendation && (
            <div className="analysis-section">
              <h4>投资建议</h4>
              <p>{analysis.investment_recommendation}</p>
            </div>
          )}

          {analysis.web_search_results && analysis.web_search_results.length > 0 && (
            <div className="analysis-section">
              <h4>相关信息</h4>
              {analysis.web_search_results.slice(0, 3).map((result, index) => (
                <div key={index} style={{ marginBottom: '8px' }}>
                  <a 
                    href={result.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    style={{ color: '#00d4ff', textDecoration: 'none' }}
                  >
                    {result.title}
                  </a>
                  <p style={{ fontSize: '0.8rem', color: '#999', marginTop: '2px' }}>
                    {result.snippet}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {token.analysisStatus === 'FAILED' && analysis?.error_message && (
        <div className="analysis-content">
          <div className="analysis-section" style={{ borderLeftColor: '#dc3545' }}>
            <h4>错误信息</h4>
            <p style={{ color: '#dc3545' }}>{analysis.error_message}</p>
          </div>
        </div>
      )}
    </div>
  );
  // return (
  //   <div className="token-card">
  //     <div className="token-header">
  //       <div className="token-info">
  //         <h3>{token.name}</h3>
  //         <p>${token.symbol}</p>
  //         <p className="token-mint">{token.mint.substring(0, 8)}...</p>
  //       </div>
  //       <div className={`token-status ${getStatusClass(token.analysisStatus)}`}>
  //         {getStatusText(token.analysisStatus)}
  //       </div>
  //     </div>

  //     {token.analysisStatus === 'ANALYZING' && (
  //       <div className="progress-bar">
  //         <div 
  //           className="progress-fill" 
  //           style={{ width: `${token.analysisProgress}%` }}
  //         ></div>
  //       </div>
  //     )}

  //     <div className="token-details">
  //       <p><strong>创建时间:</strong> {moment(token.created_at).format('YYYY-MM-DD HH:mm:ss')}</p>
  //       <p><strong>总供应量:</strong> {formatNumber(token.token_total_supply)}</p>
  //       <p><strong>虚拟SOL储备:</strong> {formatNumber(token.virtual_sol_reserves)}</p>
  //     </div>

  //     {analysis && token.analysisStatus === 'COMPLETED' && (
  //       <div className="analysis-content">
  //         {analysis.narrative_analysis && (
  //           <div className="analysis-section">
  //             <h4>叙事分析</h4>
  //             <p><strong>类别:</strong> {analysis.narrative_analysis.category}</p>
  //             <p><strong>相关性:</strong> {analysis.narrative_analysis.relevance_score}%</p>
  //             <p>{analysis.narrative_analysis.description}</p>
  //           </div>
  //         )}

  //         {analysis.risk_assessment && (
  //           <div className="analysis-section">
  //             <h4>风险评估</h4>
  //             <p>
  //               <strong>风险等级:</strong> 
  //               <span className={`risk-level ${getRiskLevelClass(analysis.risk_assessment.level)}`}>
  //                 {analysis.risk_assessment.level}
  //               </span>
  //               <span style={{ marginLeft: '10px' }}>
  //                 ({analysis.risk_assessment.score}/100)
  //               </span>
  //             </p>
  //             <p>{analysis.risk_assessment.description}</p>
  //           </div>
  //         )}

  //         {analysis.market_analysis && (
  //           <div className="analysis-section">
  //             <h4>市场分析</h4>
  //             <p><strong>流动性:</strong> {analysis.market_analysis.liquidity_analysis}</p>
  //             <p><strong>价格预测:</strong> {analysis.market_analysis.price_prediction}</p>
  //           </div>
  //         )}

  //         {analysis.ai_summary && (
  //           <div className="analysis-section">
  //             <h4>AI总结</h4>
  //             <p>{analysis.ai_summary}</p>
  //           </div>
  //         )}

  //         {analysis.investment_recommendation && (
  //           <div className="analysis-section">
  //             <h4>投资建议</h4>
  //             <p>{analysis.investment_recommendation}</p>
  //           </div>
  //         )}

  //         {analysis.web_search_results && analysis.web_search_results.length > 0 && (
  //           <div className="analysis-section">
  //             <h4>相关信息</h4>
  //             {analysis.web_search_results.slice(0, 3).map((result, index) => (
  //               <div key={index} style={{ marginBottom: '8px' }}>
  //                 <a 
  //                   href={result.url} 
  //                   target="_blank" 
  //                   rel="noopener noreferrer"
  //                   style={{ color: '#00d4ff', textDecoration: 'none' }}
  //                 >
  //                   {result.title}
  //                 </a>
  //                 <p style={{ fontSize: '0.8rem', color: '#999', marginTop: '2px' }}>
  //                   {result.snippet}
  //                 </p>
  //               </div>
  //             ))}
  //           </div>
  //         )}
  //       </div>
  //     )}

  //     {token.analysisStatus === 'FAILED' && analysis?.error_message && (
  //       <div className="analysis-content">
  //         <div className="analysis-section" style={{ borderLeftColor: '#dc3545' }}>
  //           <h4>错误信息</h4>
  //           <p style={{ color: '#dc3545' }}>{analysis.error_message}</p>
  //         </div>
  //       </div>
  //     )}
  //   </div>
  // );
};

export default TokenCard;
