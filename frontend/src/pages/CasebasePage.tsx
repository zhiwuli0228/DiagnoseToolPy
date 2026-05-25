import { Result, Button } from 'antd';
import { useTranslation } from 'react-i18next';

function CasebasePage() {
  const { t } = useTranslation();

  return (
    <div>
      <h1>{t('casebase.title')}</h1>
      <Result
        status="info"
        title={t('casebase.title')}
        subTitle="Case list and search functionality coming soon"
        extra={
          <Button type="primary" href="/">
            {t('casebase.goToDashboard')}
          </Button>
        }
      />
    </div>
  );
}

export default CasebasePage;
