import React, { useState } from 'react';
import { useLanguage, Language } from '../context/LanguageContext';
import {
  Button,
  Card,
  CardHeader,
  CardTitle,
  Input,
  Select,
  SegmentedControl,
  Checkbox,
  Modal,
  BottomSheet,
  Badge,
  Tabs,
  TabPanel,
  Table,
  Skeleton,
  Avatar,
  AlertBanner,
} from '../components/ui';
import {
  TabletIcon,
  CapsuleIcon,
  SyrupIcon,
  InjectionIcon,
  DropsIcon,
  CreamIcon,
  InhalerIcon,
  SunriseIcon,
  MiddaySunIcon,
  MoonIcon,
  BeforeFoodIcon,
  AfterFoodIcon,
  WithFoodIcon,
  ShieldSafetyIcon,
  CheckmarkIcon,
  AlertAmberIcon,
  ListenIcon,
} from '../components/icons/HealthcareIcons';
import { Volume2, Search, ArrowRight, ShieldCheck } from 'lucide-react';

export const StyleguidePage: React.FC = () => {
  const { language, setLanguage, t } = useLanguage();
  const [modalOpen, setModalOpen] = useState(false);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [segVal, setSegVal] = useState('morning');
  const [activeTab, setActiveTab] = useState('tab-buttons');
  const [chk1, setChk1] = useState(true);
  const [chk2, setChk2] = useState(false);

  const languages: { code: Language; label: string; scriptName: string }[] = [
    { code: 'en', label: 'English', scriptName: 'English' },
    { code: 'hi', label: 'Hindi', scriptName: 'हिन्दी' },
    { code: 'gu', label: 'Gujarati', scriptName: 'ગુજરાતી' },
    { code: 'mr', label: 'Marathi', scriptName: 'मराठी' },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-12 space-y-12 text-left">
      {/* Header */}
      <div className="border-b border-stone-200 pb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[#0F5147]">
            Design System · Living Component Guide
          </span>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#1C252E] mt-1">
            Prescripto 2.0 Healthcare UI
          </h1>
          <p className="text-sm text-[#4B5563] mt-1">
            Human-centered, accessible clinical components tested across all 4 Indian languages.
          </p>
        </div>

        {/* Language selector in styleguide */}
        <div className="flex items-center gap-2 bg-white p-1.5 rounded-xl border border-stone-200">
          {languages.map((l) => (
            <button
              key={l.code}
              type="button"
              onClick={() => setLanguage(l.code)}
              className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition-all min-h-[44px] cursor-pointer ${
                language === l.code
                  ? 'bg-[#0F5147] text-white shadow-2xs'
                  : 'text-[#4B5563] hover:text-[#1C252E] hover:bg-stone-100'
              }`}
            >
              {l.scriptName}
            </button>
          ))}
        </div>
      </div>

      {/* 1. Design Tokens & Color Swatches */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-[#1C252E]">1. Color Palette Tokens (WCAG AA)</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
          <div className="p-3 rounded-xl bg-white border border-stone-200 shadow-2xs">
            <div className="h-12 rounded-lg bg-[#FAF9F6] border border-stone-200" />
            <div className="mt-2 text-xs font-semibold text-[#1C252E]">Paper White</div>
            <div className="text-[11px] font-mono text-stone-500">#FAF9F6 · bg</div>
          </div>
          <div className="p-3 rounded-xl bg-white border border-stone-200 shadow-2xs">
            <div className="h-12 rounded-lg bg-[#0F5147]" />
            <div className="mt-2 text-xs font-semibold text-[#1C252E]">Clinic Green</div>
            <div className="text-[11px] font-mono text-stone-500">#0F5147 · brand</div>
          </div>
          <div className="p-3 rounded-xl bg-white border border-stone-200 shadow-2xs">
            <div className="h-12 rounded-lg bg-[#E6F0EE] border border-[#9DC1BB]" />
            <div className="mt-2 text-xs font-semibold text-[#1C252E]">Soft Green Tint</div>
            <div className="text-[11px] font-mono text-stone-500">#E6F0EE · tint</div>
          </div>
          <div className="p-3 rounded-xl bg-white border border-stone-200 shadow-2xs">
            <div className="h-12 rounded-lg bg-[#B45309]" />
            <div className="mt-2 text-xs font-semibold text-[#1C252E]">Calm Amber</div>
            <div className="text-[11px] font-mono text-stone-500">#B45309 · check</div>
          </div>
          <div className="p-3 rounded-xl bg-white border border-stone-200 shadow-2xs">
            <div className="h-12 rounded-lg bg-[#BE123C]" />
            <div className="mt-2 text-xs font-semibold text-[#1C252E]">Danger Rose</div>
            <div className="text-[11px] font-mono text-stone-500">#BE123C · error</div>
          </div>
          <div className="p-3 rounded-xl bg-white border border-stone-200 shadow-2xs">
            <div className="h-12 rounded-lg bg-[#1C252E]" />
            <div className="mt-2 text-xs font-semibold text-[#1C252E]">Deep Ink</div>
            <div className="text-[11px] font-mono text-stone-500">#1C252E · text</div>
          </div>
        </div>
      </section>

      {/* 2. Custom Healthcare Icon Set */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-[#1C252E]">2. Custom Healthcare Line Icons (1.75px Stroke)</h2>
        <Card>
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-[#4B5563] uppercase tracking-wider mb-3">
                Medicine Dosage Forms
              </h3>
              <div className="flex flex-wrap gap-6 text-center text-xs font-medium text-[#1C252E]">
                <div className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-[#FAF9F6] border border-stone-200 min-w-[80px]">
                  <TabletIcon className="text-[#0F5147]" size={28} />
                  <span>Tablet</span>
                </div>
                <div className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-[#FAF9F6] border border-stone-200 min-w-[80px]">
                  <CapsuleIcon className="text-[#0F5147]" size={28} />
                  <span>Capsule</span>
                </div>
                <div className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-[#FAF9F6] border border-stone-200 min-w-[80px]">
                  <SyrupIcon className="text-[#0F5147]" size={28} />
                  <span>Syrup</span>
                </div>
                <div className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-[#FAF9F6] border border-stone-200 min-w-[80px]">
                  <InjectionIcon className="text-[#0F5147]" size={28} />
                  <span>Injection</span>
                </div>
                <div className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-[#FAF9F6] border border-stone-200 min-w-[80px]">
                  <DropsIcon className="text-[#0F5147]" size={28} />
                  <span>Drops</span>
                </div>
                <div className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-[#FAF9F6] border border-stone-200 min-w-[80px]">
                  <CreamIcon className="text-[#0F5147]" size={28} />
                  <span>Cream</span>
                </div>
                <div className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-[#FAF9F6] border border-stone-200 min-w-[80px]">
                  <InhalerIcon className="text-[#0F5147]" size={28} />
                  <span>Inhaler</span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-[#4B5563] uppercase tracking-wider mb-3">
                Daily Schedule & Food Timing
              </h3>
              <div className="flex flex-wrap gap-6 text-center text-xs font-medium text-[#1C252E]">
                <div className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-[#FAF9F6] border border-stone-200 min-w-[80px]">
                  <SunriseIcon className="text-amber-600" size={28} />
                  <span>Morning</span>
                </div>
                <div className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-[#FAF9F6] border border-stone-200 min-w-[80px]">
                  <MiddaySunIcon className="text-amber-500" size={28} />
                  <span>Afternoon</span>
                </div>
                <div className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-[#FAF9F6] border border-stone-200 min-w-[80px]">
                  <MoonIcon className="text-indigo-600" size={28} />
                  <span>Night</span>
                </div>
                <div className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-[#FAF9F6] border border-stone-200 min-w-[80px]">
                  <BeforeFoodIcon className="text-[#0F5147]" size={28} />
                  <span>Before food</span>
                </div>
                <div className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-[#FAF9F6] border border-stone-200 min-w-[80px]">
                  <AfterFoodIcon className="text-[#0F5147]" size={28} />
                  <span>After food</span>
                </div>
                <div className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-[#FAF9F6] border border-stone-200 min-w-[80px]">
                  <WithFoodIcon className="text-[#0F5147]" size={28} />
                  <span>With food</span>
                </div>
                <div className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-[#FAF9F6] border border-stone-200 min-w-[80px]">
                  <ShieldSafetyIcon className="text-[#BE123C]" size={28} />
                  <span>Safety Only</span>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </section>

      {/* 3. Base UI Components */}
      <section className="space-y-6">
        <h2 className="text-xl font-bold text-[#1C252E]">3. Core UI Components</h2>

        <Tabs
          tabs={[
            { id: 'tab-buttons', label: 'Buttons & Badges' },
            { id: 'tab-forms', label: 'Forms & Inputs' },
            { id: 'tab-surfaces', label: 'Modals & Overlays' },
            { id: 'tab-tables', label: 'Tables & Skeletons' },
          ]}
          activeTab={activeTab}
          onChange={setActiveTab}
        />

        {/* Panel 1: Buttons & Badges */}
        <TabPanel id="tab-buttons" activeTab={activeTab}>
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-[#4B5563] mb-3">Action Buttons</h3>
              <div className="flex flex-wrap items-center gap-3">
                <Button variant="primary" leftIcon={<ListenIcon size={18} />}>
                  {t('common.listen', 'Listen in your language')}
                </Button>
                <Button variant="secondary">{t('common.cancel', 'Cancel')}</Button>
                <Button variant="outline">{t('common.edit', 'Edit Medicine')}</Button>
                <Button variant="ghost">{t('common.view', 'View Details')}</Button>
                <Button variant="destructive">{t('common.delete', 'Remove Item')}</Button>
                <Button variant="primary" isLoading>
                  Saving
                </Button>
                <Button variant="primary" disabled>
                  Disabled
                </Button>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-[#4B5563] mb-3">Status Badges</h3>
              <div className="flex flex-wrap items-center gap-2.5">
                <Badge variant="brand" dot>
                  {t('common.processing', 'Processing')}
                </Badge>
                <Badge variant="success" dot>
                  {t('common.approved', 'Ready / Approved')}
                </Badge>
                <Badge variant="warning" dot>
                  {t('common.pending', 'Needs Doctor Check')}
                </Badge>
                <Badge variant="danger" dot>
                  High Allergy Caution
                </Badge>
                <Badge variant="neutral">Walk-in Patient</Badge>
                <Badge variant="outline">PAT-1082</Badge>
              </div>
            </div>
          </div>
        </TabPanel>

        {/* Panel 2: Forms & Inputs */}
        <TabPanel id="tab-forms" activeTab={activeTab}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <Input
                label="Patient Phone Number"
                placeholder="e.g. 9876543210"
                helperText="We will send a 6-digit verification code"
                required
              />
              <Input
                label="Prescription Search"
                placeholder="Search by doctor or medicine..."
                leftIcon={<Search size={18} />}
              />
              <Input
                label="Invalid Field State"
                value="Invalid Dosage Value"
                errorMessage="Dosage must be a positive number (e.g. 500mg)"
                required
              />
            </div>

            <div className="space-y-4">
              <Select
                label="Dosage Form"
                options={[
                  { value: 'TABLET', label: 'Tablet (Oral)' },
                  { value: 'SYRUP', label: 'Syrup / Suspension' },
                  { value: 'CAPSULE', label: 'Capsule' },
                  { value: 'INJECTION', label: 'Injection / Vial' },
                ]}
                helperText="Form identified from prescription"
              />

              <div>
                <label className="block text-sm font-semibold text-[#1C252E] mb-1.5">
                  Schedule Timing (Segmented)
                </label>
                <SegmentedControl
                  value={segVal}
                  onChange={setSegVal}
                  options={[
                    { value: 'morning', label: 'Morning', icon: <SunriseIcon size={18} /> },
                    { value: 'afternoon', label: 'Afternoon', icon: <MiddaySunIcon size={18} /> },
                    { value: 'night', label: 'Night', icon: <MoonIcon size={18} /> },
                  ]}
                />
              </div>

              <div className="pt-2">
                <Checkbox
                  checked={chk1}
                  onChange={(e) => setChk1(e.target.checked)}
                  label="I understand this is a computer reading, not medical advice."
                  description="Always verify with a licensed doctor or pharmacist before taking medicines."
                />
                <Checkbox
                  checked={chk2}
                  onChange={(e) => setChk2(e.target.checked)}
                  label="Notify me when medication is due via browser alerts."
                />
              </div>
            </div>
          </div>
        </TabPanel>

        {/* Panel 3: Modals & Overlays */}
        <TabPanel id="tab-surfaces" activeTab={activeTab}>
          <div className="space-y-6">
            <div className="flex flex-wrap gap-4">
              <Button onClick={() => setModalOpen(true)}>Open Desktop / Responsive Dialog</Button>
              <Button variant="outline" onClick={() => setSheetOpen(true)}>
                Open Mobile Bottom Sheet
              </Button>
            </div>

            <div className="space-y-3">
              <AlertBanner
                type="info"
                title="Prescription Processing Note"
              >
                Computer reading takes ~10 seconds. You can edit any medicine before saving.
              </AlertBanner>
              <AlertBanner
                type="warning"
                title="Unclear Dosage in Line 2"
              >
                The doctor's handwriting is partially obscured. Please verify the photo.
              </AlertBanner>
              <AlertBanner
                type="error"
                title="Severe Drug Interaction Caution"
              >
                Paracetamol + duplicate NSAID detected. Check with doctor immediately.
              </AlertBanner>
            </div>
          </div>
        </TabPanel>

        {/* Panel 4: Tables & Skeletons */}
        <TabPanel id="tab-tables" activeTab={activeTab}>
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-[#4B5563] mb-3">Clinical Table</h3>
              <Table
                columns={[
                  {
                    key: 'patient',
                    header: 'Patient',
                    render: (item: any) => (
                      <div className="flex items-center gap-2.5">
                        <Avatar name={item.name} size="sm" />
                        <div>
                          <div className="font-semibold text-[#1C252E]">{item.name}</div>
                          <div className="text-xs text-stone-500">{item.id}</div>
                        </div>
                      </div>
                    ),
                  },
                  {
                    key: 'medicines',
                    header: 'Medicines',
                    render: (item: any) => (
                      <span className="text-sm text-stone-700">{item.meds}</span>
                    ),
                  },
                  {
                    key: 'status',
                    header: 'Status',
                    render: (item: any) => (
                      <Badge variant={item.status === 'Ready' ? 'success' : 'warning'} dot>
                        {item.status}
                      </Badge>
                    ),
                  },
                ]}
                data={[
                  { name: 'Ramesh Patel', id: 'PAT-4091', meds: 'Calpol 650mg, Pan 40', status: 'Ready' },
                  { name: 'Sunita Sharma', id: 'PAT-8812', meds: 'Augmentin 625, Montair-LC', status: 'Checking' },
                ]}
                keyExtractor={(item: any) => item.id}
              />
            </div>

            <div>
              <h3 className="text-sm font-semibold text-[#4B5563] mb-3">Layout Skeleton Loaders</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Skeleton variant="card" />
                <Skeleton variant="card" />
              </div>
            </div>
          </div>
        </TabPanel>
      </section>

      {/* Interactive Modal Demo */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Edit Medicine Schedule"
        description="Verify the dosage and timings extracted from the prescription."
        footer={
          <>
            <Button variant="secondary" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={() => setModalOpen(false)}>
              Save Changes
            </Button>
          </>
        }
      >
        <p className="text-sm text-[#4B5563]">
          This dialog is accessible, traps focus, responds to the Escape key, and renders
          cleanly across mobile and desktop viewports.
        </p>
      </Modal>

      {/* Interactive Bottom Sheet Demo */}
      <BottomSheet
        isOpen={sheetOpen}
        onClose={() => setSheetOpen(false)}
        title="Medication Details"
        subtitle="Tablet Paracetamol 650mg"
        footer={
          <Button variant="primary" className="w-full" onClick={() => setSheetOpen(false)}>
            Close Sheet
          </Button>
        }
      >
        <div className="space-y-3 text-sm text-[#4B5563]">
          <p>
            Bottom sheets slide smoothly from the bottom on mobile devices and provide an
            accessible gesture-friendly area for medicine reviews, photo viewer, and health assistant.
          </p>
        </div>
      </BottomSheet>
    </div>
  );
};

export default StyleguidePage;
